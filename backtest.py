import pandas as pd
import numpy as np
import random
import config
from data_loader import DataManager
from features import FeatureEngineer
from models import SymbolModel
from broker_client import PaperBroker
from datetime import timedelta

class Backtester:
    """
    Backtesting engine integrating Data, Model, and Broker.
    """
    
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.dm = DataManager()
        self.fe = FeatureEngineer()
        self.broker = PaperBroker(initial_balance=config.INITIAL_BALANCE)
        self.model = SymbolModel(symbol)
        self.journal = []
        self.trades_today = 0
        self.current_day = None

    def run(self):
        print(f"Starting backtest for {self.symbol}...")
        
        # 1. Load Data
        df = self.dm.fetch_data(self.symbol)
        if df.empty:
            print("No data.")
            return []

        # 2. Prepare Features
        df = self.fe.compute_features(df)
        
        # 3. Predict across history (in a real backtest, we'd do this bar-by-bar to avoid lookahead on features if any)
        # Assuming features are properly lagged.
        
        feature_cols = [c for c in df.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'target', 'future_ret']]
        X = df[feature_cols]
        
        # Ensure model is ready
        self.model.load()
        if not self.model.models:
             print("Model not trained or no horizons found. Please run training first.")
             return []

        preds_dict = self.model.predict(X)
        # probs_dict = self.model.predict_proba(X) # Not used in loop currently
        
        # Use 1H as primary signal for backtest flow, or combine.
        # Let's assume user wants to trade if ANY valid signal, or specific?
        # Defaulting to 1H for this run logic.
        preds = preds_dict.get(1, np.zeros(len(X)))
        
        df['prediction'] = preds
        
        # 4. Loop Bar-by-Bar
        for i in range(len(df)):
            if i < config.LOOKBACK_PERIOD: continue
            
            row = df.iloc[i]
            timestamp = row.name
            
            # Day tracking for trade limits
            if self.current_day != timestamp.date():
                self.current_day = timestamp.date()
                self.trades_today = 0
            
            # Monday=0, Sunday=6
            if timestamp.weekday() >= 5:
                continue

            # Check Trading Hours
            is_in_window = False
            current_time = timestamp.time()
            from datetime import time
            
            for window in config.TRADING_WINDOWS:
                start_h, start_m = window["start"]
                end_h, end_m = window["end"]
                
                start_time = time(start_h, start_m)
                end_time = time(end_h, end_m)
                
                if start_time <= current_time <= end_time:
                    is_in_window = True
                    break
            
            if not is_in_window:
                # We still process exits even outside windows? 
                # Usually yes, but user said "Trade option from...", implying entry.
                # Exits are usually allowed anytime market is open, but for simplicity let's allow exits processing
                # but SKIP ENTRY.
                self._process_exits(row['Close'], timestamp)
                continue

            current_price = row['Close']
            signal = row['prediction'] # 1=Bull, -1=Bear, 0=Neutral
            
            self._process_exits(current_price, timestamp)
            self._process_entry(signal, current_price, timestamp, None)

        print(f"Backtest complete. Final Balance: ${self.broker.get_account_balance():.2f}")
        return self.broker.trade_history

    def _process_entry(self, signal, current_price, timestamp, prob=None):
        # Check daily trade limit
        if self.trades_today >= config.MAX_TRADES_PER_DAY:
            return

        # Only one position at a time per symbol for simplicity
        if len(self.broker.get_positions()) > 0:
            return

        if signal == 0:
            return

        # Position Sizing
        balance = self.broker.get_account_balance()
        risk_pct = config.MIN_RISK_PERCENT # Can scale with confidence
        position_size_usd = balance * risk_pct
        
        # Select Option
        option_chain = self.dm.generate_option_chain(self.symbol, current_price, timestamp)
        
        if signal == 1: # Bullish -> Call
            contract_type = "call"
        else: # Bearish -> Put
            contract_type = "put"
            
        # Filter by DTE
        # Naive selection: First one in list (usually lowest DTE, ATM)
        candidates = option_chain[
            (option_chain['type'] == contract_type) & 
            (abs(option_chain['strike'] - current_price) / current_price < 0.01) # Near Money
        ]
        
        if candidates.empty:
            # Try wider
             candidates = option_chain[option_chain['type'] == contract_type]
        
        if candidates.empty:
            return 

        contract = candidates.iloc[0]
        price = contract['price']
        
        # Quantity
        qty = int(position_size_usd / price)
        if qty < 1: return
        
        # Risk Config
        sl_pct = random.uniform(config.MIN_STOP_LOSS_PERCENT, config.MAX_STOP_LOSS_PERCENT)
        # proper randomization of TP
        tp_pct = random.uniform(config.MIN_TAKE_PROFIT_PERCENT, config.MAX_TAKE_PROFIT_PERCENT)
        
        # Execute
        order = self.broker.place_order(
            symbol=contract['id'],
            quantity=qty,
            side='buy',
            price=price,
            time=timestamp,
            stop_loss=price * (1 - sl_pct),
            take_profit=price * (1 + tp_pct)
        )
        
        if order:
            self.trades_today += 1

    def _process_exits(self, underlying_price, timestamp):
        positions = self.broker.get_positions()
        if not positions:
             return
             
        # Generate current theoretical option prices for SL/TP check
        chain = self.dm.generate_option_chain(self.symbol, underlying_price, timestamp)
        
        for pos in positions:
            # Check for expiration FIRST
            expiry_str = pos['symbol'].split('_')[-1]
            try:
                expiry_date = pd.to_datetime(expiry_str)
                # Normalize expiry to EOD
                expiry_date = expiry_date.replace(hour=16, minute=0, second=0)
                
                # Ensure timestamp is comparable
                curr_ts = timestamp.replace(tzinfo=None) if hasattr(timestamp, 'replace') else timestamp
                
                if curr_ts >= expiry_date:
                    # Expired: Calculate Intrinsic
                    is_call = "_C_" in pos['symbol']
                    is_put = "_P_" in pos['symbol']
                    strike = float(pos['symbol'].split('_')[-2])
                    
                    intrinsic = 0.0
                    if is_call: intrinsic = max(0, underlying_price - strike)
                    if is_put: intrinsic = max(0, strike - underlying_price)
                    
                    self.broker.close_position(pos['id'], intrinsic, time=timestamp)
                    continue
            except Exception as e:
                print(f"Error parsing expiry: {e}")
                
            # Check SL/TP using simulated chain prices
            match = chain[chain['id'] == pos['id']]
            if not match.empty:
                current_opt_price = match.iloc[0]['price']
                
                if current_opt_price <= pos['stop_loss']:
                    self.broker.close_position(pos['id'], current_opt_price, time=timestamp)
                elif current_opt_price >= pos['take_profit']:
                    self.broker.close_position(pos['id'], current_opt_price, time=timestamp)
            else:
                 # If not in chain (e.g. DTE logic excluded it), estimate price or hold?
                 # Fallback: Estimate using Intrinsic + Time Decay? 
                 # Or just force close if we can't price it.
                 # Let's force close to be safe if data is missing, or just wait.
                 pass

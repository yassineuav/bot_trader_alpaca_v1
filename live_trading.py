import time
import pandas as pd
import schedule
from datetime import datetime
import config
from data_loader import DataManager
from features import FeatureEngineer
from models import SymbolModel
from broker_client import PaperBroker
from journal import TradeJournal

class LiveTrader:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.dm = DataManager()
        self.fe = FeatureEngineer()
        self.model = SymbolModel(symbol)
        self.broker = PaperBroker(initial_balance=config.INITIAL_BALANCE)
        self.journal = TradeJournal()
        
        self.model.load()
        if not self.model.models:
            raise ValueError(f"Model for {symbol} not found. Train first.")

    def trading_loop(self):
        print(f"Started Live/Sim Trading for {self.symbol}...")
        
        while True:
            try:
                self.on_bar()
            except Exception as e:
                print(f"Error in loop: {e}")
            
            # Wait for next check (e.g. 1 minute or 1 hour)
            time.sleep(60) 

    def on_bar(self):
        # 1. Get latest data
        df = self.dm.fetch_data(self.symbol, interval="1h") # Fetch recent
        if df.empty: return

        # 2. Features
        df = self.fe.compute_features(df)
        
        # 3. Predict (Last bar)
        feature_cols = [c for c in df.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume', 'target', 'future_ret']]
        last_row = df.iloc[[-1]][feature_cols]
        
        preds_dict = self.model.predict(last_row)
        # Use 1H as primary
        prediction = preds_dict.get(1, [0])[0]
        # proba = self.model.predict_proba(last_row)[0]

        print(f"[{datetime.now()}] Signal: {prediction}")

        # 4. Execute
        current_price = df['Close'].iloc[-1]
        self._manage_positions(current_price)
        self._execute_entry(prediction, current_price)
        
    def _execute_entry(self, signal, current_price):
        # Time Check
        now = datetime.now()
        if now.weekday() >= 5: # Sat/Sun
             return

        from datetime import time
        current_time = now.time()
        is_in_window = False
        
        for window in config.TRADING_WINDOWS:
            start_h, start_m = window["start"]
            end_h, end_m = window["end"]
            start_time_obj = time(start_h, start_m)
            end_time_obj = time(end_h, end_m)
            
            if start_time_obj <= current_time <= end_time_obj:
                is_in_window = True
                break
        
        if not is_in_window:
            # print("Outside trading hours.") # Optional noise reduction
            return

        if len(self.broker.get_positions()) > 0 or signal == 0:
            return

        # Simple Paper Entry Logic (Copy of Backtest essentially)
        print(f"Entering trade {signal}...")
        # ... logic similar to backtest ...
        # For brevity, placeholders:
        
        contract_id = f"{self.symbol}_{'C' if signal==1 else 'P'}_SIM"
        price = 1.00 # Dummy
        
        self.broker.place_order(contract_id, 10, 'buy', price=price, time=datetime.now())
        print("Order Placed.")

    def _manage_positions(self, current_price):
        # Check TP/SL
        for pos in self.broker.get_positions():
             # Logic to check real option price would accept API client here
             # Simulation: Close after 1 minute for test
             self.broker.close_position(pos['id'], pos['entry_price'] * 1.1, time=datetime.now())
             
             # Log
             last_trade = self.broker.trade_history[-1]
             self.journal.log_trade(last_trade)
             print("Position Closed and Logged.")

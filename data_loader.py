import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import config
from typing import List, Optional

class DataManager:
    """
    Handles downloading historical data and simulating options chains.
    """

    def __init__(self):
        self.data_dir = config.DATA_DIR

    def fetch_data(self, symbol: str, start_date: str = config.START_DATE, interval: str = config.INTERVAL) -> pd.DataFrame:
        """
        Downloads OHLCV data from yfinance.
        """
        print(f"Fetching data for {symbol}...")
        df = yf.download(symbol, start=start_date, interval=interval, progress=False)
        
        if df.empty:
            print(f"Warning: No data found for {symbol}")
            return df
            
        # Standardize columns (yfinance returns MultiIndex usually, sometimes needs flattening)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        # Ensure we have standard columns: Open, High, Low, Close, Volume
        df = df[['Open', 'High', 'Low', 'Close', 'Volume']]
        df.dropna(inplace=True)
        return df

    def get_latest_price(self, symbol: str) -> float:
        """
        Gets the latest real-time price (approximate via yfinance).
        """
        ticker = yf.Ticker(symbol)
        # fast_info is often faster/more reliable for latest price than history
        try:
            return ticker.fast_info['last_price']
        except:
            # Fallback to last close
            df = ticker.history(period="1d")
            if not df.empty:
                return df['Close'].iloc[-1]
            return 0.0

    def generate_option_chain(self, symbol: str, current_price: float, current_date: datetime) -> pd.DataFrame:
        """
        Simulates an options chain for backtesting/paper trading usage if real API is missing.
        Creates Calls and Puts with strikes around current_price and various DTEs.
        """
        
        # Determine DTE range based on symbol config
        dte_min, dte_max = config.DTE_RULES.get(symbol, config.DTE_RULES["DEFAULT"])
        
        chain_data = []
        
        # Generate strikes: +/- 5% range, step 1.0 (approx)
        strike_step = 1.0 if current_price < 100 else 5.0
        min_strike = int(current_price * 0.95)
        max_strike = int(current_price * 1.05)
        strikes = np.arange(min_strike, max_strike + strike_step, strike_step)
        
        # Generate varied DTEs
        # For simplicity in simulation, we issue contracts expiring today, tomorrow, etc.
        # until max_dte.
        
        for dte in range(dte_min, dte_max + 1):
             # Hypothetical expiry date
            expiry_date = current_date + timedelta(days=dte)
            
            for strike in strikes:
                # Approximate generic option price used for simulation entry
                # This is NOT Black-Scholes, just a placeholder for paper-trading logic
                # Real implementation would query an API.
                
                # Check moneyness for sensible simulated prices
                # Call Price ~ max(0, S - K) + TimeValue
                # Put Price ~ max(0, K - S) + TimeValue
                
                time_value = (dte + 1) * 0.5 # Dummy time value
                
                call_intrinsic = max(0, current_price - strike)
                put_intrinsic = max(0, strike - current_price)
                
                call_price = call_intrinsic + time_value
                put_price = put_intrinsic + time_value
                
                if call_price < 0.01: call_price = 0.01
                if put_price < 0.01: put_price = 0.01

                # Add Call
                chain_data.append({
                    "symbol": symbol,
                    "type": "call",
                    "strike": strike,
                    "expiry": expiry_date,
                    "dte": dte,
                    "price": call_price,
                    "id": f"{symbol}_C_{strike}_{expiry_date.date()}"
                })
                
                # Add Put
                chain_data.append({
                    "symbol": symbol,
                    "type": "put",
                    "strike": strike,
                    "expiry": expiry_date,
                    "dte": dte,
                    "price": put_price,
                    "id": f"{symbol}_P_{strike}_{expiry_date.date()}"
                })
                
        return pd.DataFrame(chain_data)

if __name__ == "__main__":
    # Quick test
    dm = DataManager()
    df = dm.fetch_data("SPY", start_date="2023-01-01", interval="1d")
    print(df.tail())
    chain = dm.generate_option_chain("SPY", 400.0, datetime.now())
    print(chain.head())

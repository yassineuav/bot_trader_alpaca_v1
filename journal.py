import pandas as pd
import sqlite3
import csv
import config
from datetime import datetime
from typing import Dict, List

class TradeJournal:
    """
    Logs trades to CSV and/or SQLite.
    """
    
    def __init__(self):
        self.csv_path = config.JOURNAL_DIR / "trades.csv"
        self.db_path = config.JOURNAL_DIR / "trades.db"
        self._init_storage()

    def _init_storage(self):
        # CSV Header
        if not self.csv_path.exists():
            with open(self.csv_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "symbol", "option_symbol", "direction", 
                    "entry_price", "exit_price", "size_contracts", "size_dollars",
                    "sl", "tp", "pnl", "pnl_percent", "dte", "model", "prediction", "tags"
                ])
                
        # SQLite
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS trades
                     (timestamp text, symbol text, option_symbol text, direction text,
                      entry_price real, exit_price real, size_contracts integer, size_dollars real,
                      sl real, tp real, pnl real, pnl_percent real, dte integer, 
                      model text, prediction text, tags text)''')
        conn.commit()
        conn.close()

    def log_trade(self, trade_data: Dict):
        """
        Logs a completed trade.
        """
        row = [
            str(trade_data.get("exit_time", datetime.now())),
            str(trade_data.get("symbol", "N/A")),
            str(trade_data.get("option_symbol", "N/A")),
            str(trade_data.get("direction", "LONG")),
            float(trade_data.get("entry_price", 0.0)),
            float(trade_data.get("exit_price", 0.0)),
            str(trade_data.get("quantity", 0)),
            float(trade_data.get("entry_price", 0) * trade_data.get("quantity", 0)), # size dollars
            float(trade_data.get("stop_loss", 0)),
            float(trade_data.get("take_profit", 0)),
            float(trade_data.get("pnl", 0.0)),
            float(trade_data.get("pnl_percent", 0.0)),
            int(trade_data.get("dte", 0)),
            str(trade_data.get("model", "N/A")),
            str(trade_data.get("prediction", "N/A")),
            str(trade_data.get("tags", ""))
        ]
        
        # To CSV
        with open(self.csv_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(row)
            
        # To DB
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("INSERT INTO trades VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row)
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"DB Error: {e}")

    def load_trades(self) -> pd.DataFrame:
        if self.csv_path.exists():
            return pd.read_csv(self.csv_path)
        return pd.DataFrame()

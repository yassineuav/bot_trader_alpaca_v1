from abc import ABC, abstractmethod
from typing import Dict, Any, List
import pandas as pd
import config
from datetime import datetime

class AbstractBroker(ABC):
    @abstractmethod
    def get_account_balance(self) -> float:
        pass

    @abstractmethod
    def get_positions(self) -> List[Dict]:
        pass

    @abstractmethod
    def place_order(self, symbol: str, quantity: int, side: str, order_type: str = "market", price: float = 0.0) -> Dict:
        pass
        
    @abstractmethod
    def close_position(self, position_id: str, price: float) -> Dict:
        pass

class PaperBroker(AbstractBroker):
    """
    Simulates a broker for backtesting and paper trading.
    Tracks cash and open positions in memory.
    """
    
    def __init__(self, initial_balance: float = config.INITIAL_BALANCE):
        self.cash = initial_balance
        self.positions = {} # Key: position_id, Value: Dict
        self.trade_history = []
        
    def get_account_balance(self) -> float:
        # Equity = Cash + Unrealized PnL (simplified here as just Cash + Position Value at entry or current?)
        # For simplicity in this method, return Cash. 
        # Real equity calculation requires current market prices for all positions.
        return self.cash
        
    def get_positions(self) -> List[Dict]:
        return list(self.positions.values())
        
    def place_order(self, symbol: str, quantity: int, side: str, order_type: str = "market", price: float = 0.0, **kwargs) -> Dict:
        """
        Executes a simulated order.
        side: 'buy' or 'sell'
        symbol: Option symbol id (e.g. SPY_C_400_2023-01-01)
        """
        cost = quantity * price
        
        if side == 'buy':
            if cost > self.cash:
                print(f"FAILED ORDER: Insufficient funds. Cash: {self.cash}, Cost: {cost}")
                return {}
            
            self.cash -= cost
            position_id = symbol # Simple ID
            
            # If adding to existing, average down (simplified: just track separate lots or assume 1 lot per ID)
            # Here we assume unique ID per trade instance or simple aggregation
            
            if position_id in self.positions:
                # Average price logic would go here
                pass 
                
            self.positions[position_id] = {
                "id": position_id,
                "symbol": symbol,
                "quantity": quantity,
                "entry_price": price,
                "current_price": price,
                "entry_time": kwargs.get("time", datetime.now()),
                "stop_loss": kwargs.get("stop_loss", 0),
                "take_profit": kwargs.get("take_profit", 0)
            }
            
            # print(f"[PaperBroker] BOUGHT {quantity} x {symbol} @ {price}. Cash left: {self.cash:.2f}")
            return self.positions[position_id]
            
        elif side == 'sell':
            # Logic for selling to open (shorting) not implemented for this long-only options bot
            pass
            
        return {}

    def close_position(self, position_id: str, price: str, time: datetime = None) -> Dict:
        if position_id not in self.positions:
            print(f"Error: Position {position_id} not found.")
            return {}
            
        pos = self.positions[position_id]
        quantity = pos['quantity']
        proceeds = quantity * price
        
        self.cash += proceeds
        
        pnl = proceeds - (quantity * pos['entry_price'])
        pnl_percent = (price - pos['entry_price']) / pos['entry_price']
        
        trade_record = {
            "symbol": pos['symbol'],
            "entry_time": pos['entry_time'],
            "exit_time": time or datetime.now(),
            "entry_price": pos['entry_price'],
            "exit_price": price,
            "quantity": quantity,
            "pnl": pnl,
            "pnl_percent": pnl_percent
        }
        
        # print(f"[PaperBroker] SOLD {quantity} x {pos['symbol']} @ {price}. PnL: {pnl:.2f} ({pnl_percent*100:.1f}%)")
        
        del self.positions[position_id]
        self.trade_history.append(trade_record)
        return trade_record

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.dates as mdates
import config
from datetime import timedelta

class Visualizer:
    def __init__(self):
        pass
        
    def plot_trade_pnl(self, trades: pd.DataFrame):
        if trades.empty:
            print("No trades to plot.")
            return

        plt.figure(figsize=(12, 6))
        colors = ['g' if p > 0 else 'r' for p in trades['pnl']]
        plt.bar(range(len(trades)), trades['pnl'], color=colors)
        plt.title ("PnL per Trade")
        plt.xlabel("Trade ID")
        plt.ylabel("PnL ($)")
        plt.axhline(0, color='black', linewidth=1)
        plt.savefig(config.DATA_DIR / "pnl_per_trade.png")
        print("Saved pnl_per_trade.png")
        # plt.show() # Uncomment if running locally with UI

    def plot_equity_curve(self, trades: pd.DataFrame):
        if trades.empty:
            print("No trades to plot.")
            return
            
        # Reconstruct equity curve
        # Start = 1000
        # Cumulative PnL
        
        equity = [config.INITIAL_BALANCE]
        for pnl in trades['pnl']:
            equity.append(equity[-1] + pnl)
            
        plt.figure(figsize=(12, 6))
        plt.plot(equity, marker='o')
        plt.title("Account Equity Curve")
        plt.xlabel("Trades")
        plt.ylabel("Account Balance ($)")
        plt.grid(True)
        plt.savefig(config.DATA_DIR / "equity_curve.png")
        print("Saved equity_curve.png")

    def plot_forecast(self, df: pd.DataFrame, symbol: str, predictions: dict):
        """
        Plots recent price action and prediction overlays for 1h and 4h.
        predictions: {1: 1/-1/0, 4: 1/-1/0}
        """
        # Take last 50 bars
        lookback = 50
        subset = df.iloc[-lookback:].copy()
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Plot Close Price line for simplicity (or Candles if we want)
        # Using Line for now, easier to automate perfectly.
        ax.plot(subset.index, subset['Close'], label='Price', color='white', linewidth=1)
        
        # Set dark background like the image
        ax.set_facecolor('#1e1e1e')
        fig.patch.set_facecolor('#1e1e1e')
        ax.grid(True, color='#333333')
        ax.tick_params(axis='x', colors='white')
        ax.tick_params(axis='y', colors='white')
        
        last_time = subset.index[-1]
        last_price = subset['Close'].iloc[-1]
        
        # Draw Overlays for each horizon
        # To avoid overlapping, we might offset them or just draw them.
        # Image shows boxes extending into future.
        
        for h in [1, 4]:
            pred = predictions.get(h, 0)
            if hasattr(pred, "__iter__"): pred = pred[0] # handle array
            
            if pred == 0: continue
            
            threshold = config.TARGET_THRESHOLDS.get(h, 0.0)
            target_price = last_price * (1 + (threshold if pred == 1 else -threshold))
            
            # Box dimensions
            # Width = horizon hours (approx)
            # We need to map time to x-axis properly. 
            # Since index is datetime, we can use timedelta.
            
            # Ideally we simply assume 'h' bars width if index is uniform. 
            # But matplotlib date handling can be tricky.
            # Let's use simple data mapping:
            # We can't easily draw 'future' on DateAxis without adding future dates to plot limits.
            
            start_date = mdates.date2num(last_time)
            # Assuming hourly bars, h is hours.
            # We add h/24 days
            
            # Adjust duration based on interval (config says 1h)
            duration_days = h * (1/24.0) 
            end_date = start_date + duration_days
            
            width = end_date - start_date
            height = target_price - last_price
            
            # Color: Green for Long, Red for Short
            color = "#00ff00" if pred == 1 else "#ff0000"
            alpha = 0.3 if h == 4 else 0.5 # Fade larger horizon slightly?
            
            # Box
            rect = patches.Rectangle(
                (start_date, last_price), 
                width, 
                height, 
                linewidth=1, 
                edgecolor=color, 
                facecolor=color, 
                alpha=0.3
            )
            ax.add_patch(rect)
            
            # Arrow
            ax.annotate(
                '', 
                xy=(end_date, target_price), 
                xytext=(start_date, last_price),
                arrowprops=dict(facecolor=color, edgecolor=color, arrowstyle='->', lw=2)
            )
            
            # Text Tag
            ax.text(
                end_date, 
                target_price, 
                f"{h}H {'Call' if pred == 1 else 'Put'}\nTarget: {target_price:.2f}", 
                color=color, 
                fontsize=9, 
                verticalalignment='bottom' if pred==1 else 'top'
            )

        # Extend X axis to show future
        ax.set_xlim(subset.index[0], last_time + timedelta(hours=6))
        
        plt.title(f"{symbol} Forecast Analysis", color='white')
        plt.tight_layout()
        save_path = config.DATA_DIR / f"{symbol}_forecast.png"
        plt.savefig(save_path)
        print(f"Saved forecast chart to {save_path}")

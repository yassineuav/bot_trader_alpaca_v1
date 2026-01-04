import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
import config
from data_loader import DataManager
import argparse
from datetime import datetime, timedelta

def plot_all_trades(symbol="IWM"):
    # 1. Load Trades
    csv_path = config.JOURNAL_DIR / symbol / "trades.csv"
    if not csv_path.exists():
        print(f"No trades.csv found at {csv_path}")
        return

    df_trades = pd.read_csv(csv_path)
    if df_trades.empty:
        print("Trades file is empty.")
        return
        
    # Convert timestamps
    df_trades['entry_time'] = pd.to_datetime(df_trades['entry_time'])
    df_trades['exit_time'] = pd.to_datetime(df_trades['exit_time'])
    
    # Filter for symbol if needed (though mostly IWM)
    # df_trades = df_trades[df_trades['symbol'].str.contains(symbol, case=False)]
    
    # 2. Fetch Price Data covering the range
    start_date = df_trades['entry_time'].min() - timedelta(days=5)
    end_date = df_trades['exit_time'].max() + timedelta(days=5)
    
    print(f"Fetching data for {symbol} from {start_date.date()} to {end_date.date()}...")
    dm = DataManager()
    # Fetch ample data. DataManager might process 'start'/'end' args?
    # Looking at data_loader, usually it fetches period='max' or similar. 
    # Let's fetch standard and slice locally.
    df_price = dm.fetch_data(symbol)
    
    if df_price.empty:
        print("No price data found.")
        return

    # Slice price data
    # Ensure timezone awareness matches
    if df_price.index.tz is None and df_trades['entry_time'].dt.tz is not None:
        df_price.index = df_price.index.tz_localize('UTC') # Assumption
    
    mask = (df_price.index >= start_date) & (df_price.index <= end_date)
    df_price = df_price.loc[mask]
    
    if df_price.empty:
        print("Price data empty after slicing. Check timezones.")
        # Fallback: ignore dates, just plot all?
        # df_price = dm.fetch_data(symbol) 
    
    # 3. Setup Plot
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(20, 10))
    
    # Plot Price
    ax.plot(df_price.index, df_price['Close'], color='white', linewidth=1, label=f'{symbol} Price')
    
    # Plot Trades
    print(f"Plotting {len(df_trades)} trades...")
    
    for _, trade in df_trades.iterrows():
        entry_time = trade['entry_time']
        exit_time = trade['exit_time']
        entry_price = trade['entry_price'] # Option Price?
        # Wait. 'entry_price' in CSV is OPTION price (e.g. 1.38).
        # We want to plot on the UNDERLYING chart.
        # We don't have underlying entry price logged in CSV!
        # We only have option price.
        # BUT, usually we want to see the trade on the stock chart.
        # We can find the underlying price at entry_time from df_price.
        
        # Approximate underlying price
        try:
            # Find closest price row
            idx_entry = df_price.index.get_indexer([entry_time], method='nearest')[0]
            price_at_entry = df_price['Close'].iloc[idx_entry]
            
            idx_exit = df_price.index.get_indexer([exit_time], method='nearest')[0]
            price_at_exit = df_price['Close'].iloc[idx_exit]
            
        except Exception as e:
            # print(f"Skip trade {entry_time}: {e}")
            continue

        pnl = trade['pnl']
        pnl_pct = trade['pnl_percent'] * 100
        is_win = pnl > 0
        color = '#00ff00' if is_win else '#ff0000'
        
        # Draw Box (Time span + Price span?)
        # On stock chart, maybe draw box from Entry Price to Exit Price?
        # But we long/short.
        # Call: Profit if Exit > Entry.
        # Put: Profit if Exit < Entry.
        
        # Let's map it:
        # Start (x, y) = (entry_time, price_at_entry)
        # End (x, y) = (exit_time, price_at_exit)
        
        width = mdates.date2num(exit_time) - mdates.date2num(entry_time)
        height = price_at_exit - price_at_entry
        
        # Create Rectangle
        # anchor is bottom-left. for rectangle.
        # If height is negative, we need to adjust anchor.
        
        rect_start_y = price_at_entry
        if height < 0:
             rect_start_y = price_at_exit
             height = abs(height)
             
        # But for Box, visual correctness:
        # PnL > 0 (Win): Box should look Green.
        
        rect = patches.Rectangle(
            (mdates.date2num(entry_time), rect_start_y),
            width,
            height,
            linewidth=1,
            edgecolor=color,
            facecolor=color,
            alpha=0.3
        )
        ax.add_patch(rect)
        
        # Connection Line (Diagonal)
        # ax.plot([entry_time, exit_time], [price_at_entry, price_at_exit], color=color, linestyle='--', linewidth=1)
        
        # Text Annotation
        # "[date] [call/put] [strike] [pnl%]"
        # Strike is in symbol: iwm_C_212.0_...
        try:
            parts = trade['symbol'].split('_') 
            # e.g. iwm_C_212.0_2025-02-28
            otype = "CALL" if parts[1]=='C' else "PUT"
            strike = parts[2]
        except:
            otype = "OPT"
            strike = "?"
            
        label = f"[{entry_time.strftime('%m-%d %H:%M')}] [{otype}] ${strike} [{pnl_pct:.1f}%]"
        
        # Place text above or below
        text_y = max(price_at_entry, price_at_exit) * 1.01 if is_win else min(price_at_entry, price_at_exit) * 0.99
        
        # Only annotate massive wins or sparsely? Too many trades overlap.
        # Let's annotate all but small font.
        ax.text(entry_time, text_y, label, color=color, fontsize=8, rotation=45)

    # Styling
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)
    plt.grid(True, color='#333333')
    plt.title(f"{symbol} All Trades Analysis", color='white', fontsize=16)
    plt.tight_layout()
    
    out_path = config.DATA_DIR / f"{symbol}_all_trades_chart.png"
    plt.savefig(out_path)
    print(f"Saved chart to {out_path}")

if __name__ == "__main__":
    plot_all_trades("IWM")

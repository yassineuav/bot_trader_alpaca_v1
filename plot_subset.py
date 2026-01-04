import pandas as pd
import matplotlib.pyplot as plt
import config

file_path = config.JOURNAL_DIR / "trades_18_50_analysis.csv"

try:
    df = pd.read_csv(file_path)
    if df.empty:
        print("No data to plot.")
        exit()

    # Settings
    plt.style.use('dark_background')
    
    # 1. PnL per Trade
    plt.figure(figsize=(12, 6))
    colors = ['#00ff00' if p > 0 else '#ff0000' for p in df['pnl']]
    plt.bar(df.index, df['pnl'], color=colors, alpha=0.7)
    plt.title("PnL per Trade (Trades 18-50)", color='white', fontsize=14)
    plt.xlabel("Trade Index (Relative)", color='white')
    plt.ylabel("PnL ($)", color='white')
    plt.axhline(0, color='gray', linewidth=0.5)
    plt.grid(axis='y', alpha=0.2)
    
    pnl_path = config.DATA_DIR / "trades_18_50_pnl.png"
    plt.savefig(pnl_path)
    print(f"Saved {pnl_path}")
    
    # 2. Equity Curve (Reconstructed)
    # We don't know the exact starting balance of trade #18 easily without replay,
    # but we can show cumulative PnL gain relative to start of this period.
    
    cumulative_pnl = df['pnl'].cumsum()
    
    plt.figure(figsize=(12, 6))
    plt.plot(df.index, cumulative_pnl, marker='o', color='#00ccff', linewidth=2)
    plt.fill_between(df.index, cumulative_pnl, 0, alpha=0.1, color='#00ccff')
    plt.title("Cumulative PnL (Trades 18-50)", color='white', fontsize=14)
    plt.xlabel("Trade Index (Relative)", color='white')
    plt.ylabel("Cumulative Profit ($)", color='white')
    plt.grid(True, alpha=0.2)
    
    equity_path = config.DATA_DIR / "trades_18_50_equity.png"
    plt.savefig(equity_path)
    print(f"Saved {equity_path}")

except Exception as e:
    print(f"Error: {e}")

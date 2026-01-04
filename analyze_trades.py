import pandas as pd
import config

file_path = config.JOURNAL_DIR / "trades.csv"
output_path = config.JOURNAL_DIR / "trades_18_50_analysis.csv"

try:
    df = pd.read_csv(file_path)
    
    # Filter 18-50
    # User said "trades number 18 to 50". Assuming 1-based indexing from the CSV structure.
    # Rows 0-16 are first 17 trades. Row 17 is the 18th trade.
    # Row 49 is the 50th trade.
    subset = df.iloc[17:50].copy()
    
    if subset.empty:
        print("No trades found in range 18-50.")
    else:
        # Save filtered data
        subset.to_csv(output_path, index=False)
        print(f"Saved filtered trades to {output_path}")
        
        # Analysis
        total_pnl = subset['pnl'].sum()
        win_rate = (subset['pnl'] > 0).mean() * 100
        avg_pnl = subset['pnl'].mean()
        best_trade = subset.loc[subset['pnl'].idxmax()]
        worst_trade = subset.loc[subset['pnl'].idxmin()]
        
        print("\n--- Analysis of Trades 18-50 ---")
        print(f"Total Trades: {len(subset)}")
        print(f"Total PnL: ${total_pnl:,.2f}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Average PnL: ${avg_pnl:,.2f}")
        
        print("\n--- Best Trade ---")
        print(best_trade)
        
        print("\n--- Worst Trade ---")
        print(worst_trade)
        
        # Correlation with "Price" (if high priced options did better?)
        # Correlation with Direction
        
        long_calls = subset[subset['option_symbol'].str.contains("_C_")]
        long_puts = subset[subset['option_symbol'].str.contains("_P_")]
        
        print(f"\nCall PnL: ${long_calls['pnl'].sum():,.2f} ({len(long_calls)} trades)")
        print(f"Put PnL: ${long_puts['pnl'].sum():,.2f} ({len(long_puts)} trades)")

except Exception as e:
    print(f"Error: {e}")

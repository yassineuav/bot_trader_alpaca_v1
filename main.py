import argparse
import sys
import config
from training import run_training_pipeline
from backtest import Backtester
from live_trading import LiveTrader
from visualization import Visualizer
from data_loader import DataManager
from features import FeatureEngineer
from models import SymbolModel
from journal import TradeJournal
import pandas as pd

def main():
    parser = argparse.ArgumentParser(description="Options Trading Bot CLI")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Train
    train_parser = subparsers.add_parser("train", help="Train ML models")
    train_parser.add_argument("--symbol", type=str, default="SPY", help="Symbol to train")

    # Backtest
    bt_parser = subparsers.add_parser("backtest", help="Run backtest")
    bt_parser.add_argument("--symbol", type=str, default="SPY", help="Symbol to backtest")
    
    # Live
    live_parser = subparsers.add_parser("live", help="Run live/simulated trading")
    live_parser.add_argument("--symbol", type=str, default="SPY", help="Symbol to trade")
    
    # Plot
    plot_parser = subparsers.add_parser("plot", help="Generate performance charts")
    
    # Metrics
    # Predict
    predict_parser = subparsers.add_parser("predict", help="Predict and plot forecast")
    predict_parser.add_argument("--symbol", type=str, default="SPY", help="Symbol to predict")

    args = parser.parse_args()
    
    if args.command == "train":
        run_training_pipeline(args.symbol)
        
    elif args.command == "predict":
        symbol = args.symbol
        print(f"Generating forecast for {symbol}...")
        
        # 1. Data
        dm = DataManager()
        df = dm.fetch_data(symbol)
        if df.empty:
            print("No data found.")
            return

        # 2. Features
        fe = FeatureEngineer()
        df = fe.compute_features(df)
        
        # 3. Model
        model = SymbolModel(symbol)
        # Prepare last row
        feature_cols = [c for c in df.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume'] and not c.startswith('target') and not c.startswith('future_ret')]
        last_row = df.iloc[[-1]][feature_cols]
        
        predictions = model.predict(last_row)
        # Flatten predictions if they are arrays
        flat_preds = {}
        for h, v in predictions.items():
            flat_preds[h] = v[0] if hasattr(v, "__iter__") else v
            
        print(f"Predictions: {flat_preds}")
        
        # 4. Viz
        viz = Visualizer()
        viz.plot_forecast(df, symbol, flat_preds)
        
    elif args.command == "backtest":
        bt = Backtester(args.symbol)
        trades = bt.run()
        print(f"Backtest finished. {len(trades)} trades executed.")
        
        # Log to journal
        journal = TradeJournal()
        for t in trades:
            t['tags'] = 'backtest'
            journal.log_trade(t)
            
    elif args.command == "live":
        lt = LiveTrader(args.symbol)
        lt.trading_loop()
        
    elif args.command == "plot":
        journal = TradeJournal()
        trades = journal.load_trades()
        viz = Visualizer()
        viz.plot_trade_pnl(trades)
        viz.plot_equity_curve(trades)
        
    elif args.command == "metrics":
        journal = TradeJournal()
        trades = journal.load_trades()
        if not trades.empty:
            print(trades.describe())
            print(f"Total PnL: {trades['pnl'].sum():.2f}")
        else:
            print("No trades found.")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()

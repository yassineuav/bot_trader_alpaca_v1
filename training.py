import argparse
import config
from data_loader import DataManager
from features import FeatureEngineer
from models import SymbolModel

def run_training_pipeline(symbol: str):
    """
    Full training pipeline: fetch data -> clean -> feature engineer -> train -> save.
    """
    dm = DataManager()
    fe = FeatureEngineer()
    
    # 1. Fetch Data
    df = dm.fetch_data(symbol)
    if df.empty:
        print(f"Error: No data for {symbol}")
        return

    # 2. Features
    df = fe.compute_features(df)
    
    # 3. Targets
    df = fe.generate_targets(df)
    
    # CLEAN DATA: distinct handling for infinite values which might break sklearn
    import numpy as np
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    df.dropna(inplace=True)
    
    # 4. Train
    model = SymbolModel(symbol, model_type="gb")
    model.train(df)
    print(f"Training complete for {symbol}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, default="SPY", help="Symbol to train")
    args = parser.parse_args()
    
    run_training_pipeline(args.symbol)

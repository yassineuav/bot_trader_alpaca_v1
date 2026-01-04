import os
import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import TimeSeriesSplit, RandomizedSearchCV
from sklearn.metrics import accuracy_score, classification_report
import config

class SymbolModel:
    """
    Wrapper for symbol-specific ML models (Multi-Horizon).
    """
    
    def __init__(self, symbol: str, model_type: str = "rf"):
        self.symbol = symbol
        self.model_type = model_type
        # Dictionary to hold models for each horizon: {1: model_obj, 4: model_obj}
        self.models = {} 
        
    def _get_base_model(self):
        if self.model_type == "rf":
            return RandomForestClassifier(n_estimators=200, class_weight='balanced', random_state=42)
        elif self.model_type == "gb":
            return GradientBoostingClassifier(n_estimators=100, random_state=42)
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")

    def train(self, df: pd.DataFrame):
        """
        Trains separate models for each horizon.
        df must contain features and 'target_{h}h' columns.
        """
        print(f"Training models for {self.symbol}...")
        
        feature_cols = [c for c in df.columns if c not in ['Open', 'High', 'Low', 'Close', 'Volume'] and not c.startswith('target') and not c.startswith('future_ret')]
        
        X = df[feature_cols]

        for h in config.TARGET_HORIZONS:
            target_col = f"target_{h}h"
            if target_col not in df.columns:
                print(f"Skipping horizon {h}h: Target column missing.")
                continue
                
            y = df[target_col]
            
            print(f"--- Training {h}h Horizon ---")
            
            # Simple split for validation metrics (last 20%)
            split_idx = int(len(X) * 0.8)
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            model = self._get_base_model()
            model.fit(X_train, y_train)
            
            # Evaluate
            preds = model.predict(X_test)
            acc = accuracy_score(y_test, preds)
            print(f"[{self.symbol} {h}h] Test Accuracy: {acc:.4f}")
            print(classification_report(y_test, preds))
            
            # Retrain on full data
            print(f"[{self.symbol} {h}h] Retraining on full dataset...")
            model.fit(X, y)
            self.models[h] = model
            
        self.save()

    def predict(self, X_new: pd.DataFrame) -> dict:
        """
        Returns predictions for all horizons: {1: pred_array, 4: pred_array}
        """
        if not self.models:
            self.load()
            
        results = {}
        for h, model in self.models.items():
            if model:
                results[h] = model.predict(X_new)
        return results
    
    def predict_proba(self, X_new: pd.DataFrame) -> dict:
        if not self.models:
            self.load()
            
        results = {}
        for h, model in self.models.items():
            if model:
                results[h] = model.predict_proba(X_new)
        return results

    def save(self):
        for h, model in self.models.items():
            path = config.MODELS_DIR / f"{self.symbol}_model_{h}h.pkl"
            joblib.dump(model, path)
            print(f"Model saved to {path}")

    def load(self):
        self.models = {}
        for h in config.TARGET_HORIZONS:
            path = config.MODELS_DIR / f"{self.symbol}_model_{h}h.pkl"
            if path.exists():
                self.models[h] = joblib.load(path)
                # print(f"Model loaded: {path}")
            else:
                print(f"Warning: No model found at {path}")

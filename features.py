import pandas as pd
import numpy as np
import config

class FeatureEngineer:
    """
    Generates technical indicators and target labels.
    """
    
    def __init__(self):
        pass

    def compute_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds technical indicators to the DataFrame.
        """
        df = df.copy()
        
        # 1. log Returns
        df['log_ret'] = np.log(df['Close'] / df['Close'].shift(1))
        
        # 2. Moving Averages
        for period in [9, 20, 50, 200]:
            df[f'SMA_{period}'] = df['Close'].rolling(window=period).mean()
        
        # 3. RSI
        df['RSI'] = self.compute_rsi(df['Close'], 14)
        
        # 4. MACD
        exp12 = df['Close'].ewm(span=12, adjust=False).mean()
        exp26 = df['Close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp12 - exp26
        df['MACD_Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        
        # 5. Bollinger Bands
        period = 20
        df['BB_Mid'] = df['Close'].rolling(window=period).mean()
        df['BB_Std'] = df['Close'].rolling(window=period).std()
        df['BB_Upper'] = df['BB_Mid'] + (2 * df['BB_Std'])
        df['BB_Lower'] = df['BB_Mid'] - (2 * df['BB_Std'])
        df['BB_Width'] = (df['BB_Upper'] - df['BB_Lower']) / df['BB_Mid']
        
        # 6. ATR
        df['ATR'] = self.compute_atr(df, 14)
        
        # 7. Volume Change
        df['Vol_Change'] = df['Volume'].pct_change()

        # 8. Momentum (ROC)
        df['Momentum_10'] = df['Close'] / df['Close'].shift(10) - 1
        
        # 9. Volatility Ratio (Short term / Long term)
        df['Vol_Ratio'] = df['Close'].rolling(5).std() / df['Close'].rolling(20).std()
        
        # Drop NaN and Inf
        df.replace([np.inf, -np.inf], np.nan, inplace=True)
        df.dropna(inplace=True)
        return df

    def compute_rsi(self, series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff(1)
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))

    def compute_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df['High']
        low = df['Low']
        close = df['Close'].shift(1)
        
        tr1 = high - low
        tr2 = (high - close).abs()
        tr3 = (low - close).abs()
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    def generate_targets(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates 'target_N' columns for each horizon in config.
        """
        valid_rows = df.index
        
        for h in config.TARGET_HORIZONS:
            threshold = config.TARGET_THRESHOLDS.get(h, 0.002)
            
            # Future return over 'h' bars
            col_ret = f'future_ret_{h}h'
            col_target = f'target_{h}h'
            
            df[col_ret] = df['Close'].shift(-h) / df['Close'] - 1
            
            conditions = [
                (df[col_ret] > threshold),
                (df[col_ret] < -threshold)
            ]
            choices = [1, -1] # 1=Bull, -1=Bear
            
            df[col_target] = np.select(conditions, choices, default=0)
            
            # Update valid rows to ensure we don't train on NaNs
            # The last 'h' rows will have NaN for this horizon
            valid_rows = valid_rows.intersection(df.dropna(subset=[col_ret]).index)

        # We drop rows that have NaN in ANY target (intersection of validity)
        # Or we can keep them and handle NaNs during training selection.
        # For simplicity, let's just drop the max horizon Nans to support all targets.
        
        max_h = max(config.TARGET_HORIZONS)
        df = df.iloc[:-max_h] 
        
        return df

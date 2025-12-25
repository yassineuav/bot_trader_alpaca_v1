import os
from pathlib import Path

# --- Project Paths ---
BASE_DIR = Path(__file__).parent.resolve()
DATA_DIR = BASE_DIR / "data"
MODELS_DIR = BASE_DIR / "models"
JOURNAL_DIR = DATA_DIR / "journal"

# Create directories if they don't exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODELS_DIR.mkdir(parents=True, exist_ok=True)
JOURNAL_DIR.mkdir(parents=True, exist_ok=True)

# --- Trading Configuration ---
INITIAL_BALANCE = 1000.0

# Symbols to trade
SYMBOLS = ["SPY", "IWM", "AAPL", "NVDA", "TSLA"]

# Risk Management
MIN_RISK_PERCENT = 0.20  # 20% of account (Fixed)
MAX_RISK_PERCENT = 0.20  # 20% of account

MIN_STOP_LOSS_PERCENT = 0.10   # 10% loss
MAX_STOP_LOSS_PERCENT = 0.20   # 20% loss

MIN_TAKE_PROFIT_PERCENT = 0.50  # 50% gain
MAX_TAKE_PROFIT_PERCENT = 5.0   # 500% gain

MAX_TRADES_PER_DAY = 5

# DTE Rules (Days to Expiration)
# Swing Trading: 0-4 DTE
DTE_RULES = {
    "SPY": (0, 4),
    "IWM": (0, 4),
    "DEFAULT": (0, 4)
}

# Trading Hours (ET)
TRADING_WINDOWS = [
    {"start": (9, 30), "end": (11, 0)},
    {"start": (14, 0), "end": (16, 0)}
]

# Feature Engineering Config
LOOKBACK_PERIOD = 50 # bars for some indicators
# TARGET_HORIZON = 5   # DEPRECATED
TARGET_HORIZONS = [1, 4]   # Predict 1h and 4h
TARGET_THRESHOLDS = {
    1: 0.002, # 0.2% for 1h
    4: 0.005  # 0.5% for 4h
}

# Data Download Config
START_DATE = "2025-01-01"
INTERVAL = "1h" # using 1 hour bars for this example to have enough history quickly

# Broker / Live Config
PAPER_TRADING = True

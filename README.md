# 🤖 ML Options Trading Bot

A comprehensive automated trading system for options, featuring multi-horizon Machine Learning prediction, backtesting, live simulation, and detailed performance visualization.

## 🌟 Features

*   **Multi-Horizon Prediction**: Trains separate Gradient Boosting models to predict price movements for **1-hour** and **4-hour** horizons.
*   **Automated Workflow**: Single command (`run-all`) to Train -> Backtest -> Journal -> Visualize.
*   **Backtesting Engine**: Simulates options trading with realistic slippage, time-decay (DTE), and risk management rules.
*   **Risk Management**:
    *   **Dynamic Position Sizing**: Risk a fixed % of account per trade.
    *   **Auto-SL/TP**: Randomized Take Profit & Stop Loss within healthy ranges to simulate realistic variance.
    *   **Blow-Up Protection**: Auto-stops simulations if equity hits $0.
*   **Journaling**: Automatically logs all trades to CSV and SQLite in `data/journal/[Symbol]/`.
*   **Visualization**:
    *   **Forecast Charts**: Real-time prediction overlays with directional arrows.
    *   **Performance Charts**: PnL per trade, Equity Curve, and "All Trades" overlay on price action.
    *   **Metrics**: Summary statistics of trading performance.

## 🛠️ Installation

1.  **Prerequisites**: Python 3.8+
2.  **Install Dependencies**:
    ```bash
    pip install pandas numpy matplotlib scikit-learn yfinance joblib schedule
    ```

## 🚀 Usage

The bot is controlled via the Command Line Interface (CLI) in `main.py`.

### Full Pipeline (Recommended)
Trains models, runs backtest, logs trades, and generates all charts in one go.
```bash
python main.py run-all --symbol SPY
```
**Output Artifacts:** `data/journal/SPY/trades.csv`, `data/SPY_all_trades_chart.png`, `data/equity_curve.png`

### Individual Commands

| Command | Description | Example |
| :--- | :--- | :--- |
| **`train`** | Retrains the ML models for a specific symbol. | `python main.py train --symbol SPY` |
| **`backtest`** | Runs the strategy on historical data using trained models. | `python main.py backtest --symbol SPY` |
| **`predict`** | Generates a current prediction and visualizes the forecast. | `python main.py predict --symbol SPY` |
| **`plot`** | Generates PnL and Equity charts from the existing journal. | `python main.py plot --symbol SPY` |
| **`metrics`** | Shows summary metrics (win rate, total PnL, etc.) from the journal. | `python main.py metrics --symbol SPY` |
| **`live`** | Starts the live trading loop (paper trading mode). | `python main.py live --symbol SPY` |

## ⚙️ Configuration

All strategy settings are managed in `config.py`:

*   **Trading Variables**:
    *   `INITIAL_BALANCE`: Starting cash (default: $1000).
    *   `SYMBOLS`: List of valid symbols (e.g., SPY, IWM).
*   **Risk Management**:
    *   `MIN_RISK_PERCENT` / `MAX_RISK_PERCENT`: Position sizing.
    *   `MIN_STOP_LOSS_PERCENT`: Stop Loss trigger.
    *   `MIN_TAKE_PROFIT_PERCENT`: Take Profit trigger.
*   **Model Config**:
    *   `TARGET_HORIZONS`: Timeframes to predict (default: 1h, 4h).
    *   `TARGET_THRESHOLDS`: Minimum price move to count as a signal.
*   **Execution**:
    *   `PAPER_TRADING`: Set to `True` for simulation, `False` for real (requires broker implementation).

## 📂 Directory Structure

```text
├── main.py              # CLI Entry point
├── config.py            # Configuration settings
├── backtest.py          # Backtesting engine logic
├── live_trading.py      # Live execution loop
├── models.py            # ML Model (Gradient Boosting) definition
├── features.py          # Indicator & Feature engineering
├── data_loader.py       # Data fetching (yfinance)
├── visualization.py     # Plotting functions (Equity, PnL)
├── plot_all_trades.py   # Advanced chart overlays
├── journal.py           # Trade logging (CSV/SQL)
└── data/                # Generated data & charts
    └── journal/         # Trade logs per symbol
```

## ⚠️ Disclaimer
*This software is for educational purposes only. Do not risk money you cannot afford to lose. Past performance is not indicative of future results.*

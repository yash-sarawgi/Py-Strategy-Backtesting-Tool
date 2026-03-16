# Py-Strategy-Backtesting-Tool

A **Python GUI-based strategy backtesting environment** designed for
quick testing of trading strategies, trade analysis, and performance
visualization.

The tool allows users to load OHLCV datasets, write strategy logic
directly in Python, and evaluate performance through an interactive
dashboard.

------------------------------------------------------------------------

## ⚠️ Project Status

**This project is currently under development.**

Some features may still be incomplete and bugs or unexpected behavior
may occur.

Contributions, suggestions, and improvements are welcome.

------------------------------------------------------------------------

## Features

-   GUI-based backtesting dashboard
-   Strategy scripting using Python
-   Signal-based trade execution
-   Equity curve visualization
-   Drawdown analysis
-   Trade performance metrics
-   Trade log export
-   Time-based trade analysis
-   Statistical distribution analysis
-   Built-in synthetic data generator

------------------------------------------------------------------------

## Project Structure

    Py-Strategy-Backtesting-Tool/

    backtesting_dashboard.py      # Main GUI + backtesting engine
    generate_sample_data.py       # Synthetic OHLCV data generator
    EXAMPLE_STRATEGIES.md         # Example strategies
    TROUBLESHOOTING.md            # Common issues and fixes
    requirements.txt              # Python dependencies
    sample_data_trending.csv      # Example dataset

------------------------------------------------------------------------

## Installation

Clone the repository:

``` bash
git clone https://github.com/<your-username>/Py-Strategy-Backtesting-Tool.git
cd Py-Strategy-Backtesting-Tool
```

Install dependencies:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## Running the Dashboard

Start the application:

``` bash
python backtesting_dashboard.py
```

Steps:

1.  Load a CSV dataset
2.  Write or paste a strategy
3.  Run the backtest
4.  Analyze results through the dashboard tabs

------------------------------------------------------------------------

## Data Format

The tool expects CSV data containing timestamp and OHLCV fields.

Example:

    timestamp,open,high,low,close,volume
    2023-01-01 09:30:00,100,101,99,100.5,1200
    2023-01-01 09:31:00,100.5,102,100,101.3,950

------------------------------------------------------------------------

## Strategy Signal Format

Strategies must generate signals in the following format:

``` python
signals.append({
    "timestamp": timestamp,
    "type": "BUY",
    "price": price
})
```

or

``` python
signals.append({
    "timestamp": timestamp,
    "type": "SELL",
    "price": price
})
```

Example strategies are available in **EXAMPLE_STRATEGIES.md**.

------------------------------------------------------------------------

## Generating Sample Data

You can generate test datasets using:

``` bash
python generate_sample_data.py
```

This will generate synthetic OHLCV datasets useful for testing
strategies.

------------------------------------------------------------------------

## Contributing

Contributions are welcome.

If you would like to improve the project:

-   Open an issue
-   Submit a pull request
-   Suggest improvements

------------------------------------------------------------------------

## Ideas for Future Improvements

-   Additional backtest parameters
-   Transaction cost and slippage modeling
-   Advanced position sizing
-   Portfolio backtesting
-   Multi-asset testing
-   PDF performance reports
-   Multiple backtest result combiner (summary view)
-   Strategy optimization tools

------------------------------------------------------------------------

## Disclaimer

This tool is intended for **research and educational purposes only**.

It should **not be used as financial advice or live trading software**.

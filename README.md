# META Stock Data Fetcher

This Python script fetches META stock data at one-minute intervals using the yfinance library and saves it to a CSV file.

## Requirements

- Python 3.9+
- yfinance
- pandas

## Installation

1. Clone this repository
2. Install dependencies:

```
pip install yfinance pandas
```

## Usage

Run the script:

```
python meta_stock_data_fetcher.py
```

The script will continuously fetch META stock data every minute and save it to a CSV file named `META_stock_data_YYYYMMDD_HHMMSS.csv` in the same directory.

Press Ctrl+C to stop the script.

## Customization

Modify the `main()` function to change the ticker symbol, interval, or duration as needed.
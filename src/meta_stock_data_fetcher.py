import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import pytz

def fetch_stock_data(ticker, interval, timezone):
    stock = yf.Ticker(ticker)
    end_time = datetime.now(timezone)
    start_time = end_time - timedelta(minutes=1)
    data = stock.history(start=start_time, end=end_time, interval=interval)
    return data

def save_to_csv(data, filename):
    if not data.empty:
        data['Time_Zone'] = 'US'
        data.to_csv(filename)
        print(f"Data saved to {filename}")
    else:
        print("No data to save.")

def main():
    ticker = "META"
    interval = "1m"
    timezone = pytz.timezone('Europe/Paris')

    while True:
        try:
            # Wait until the start of the next minute
            now = datetime.now(timezone)
            sleep_time = 60 - now.second
            time.sleep(sleep_time)

            output_file = f"{ticker}_stock_data_{datetime.now(timezone).strftime('%Y%m%d_%H%M%S')}.csv"
            data = fetch_stock_data(ticker, interval, timezone)
            save_to_csv(data, output_file)
        except Exception as e:
            print(f"An error occurred: {e}")
            break

if __name__ == "__main__":
    main()
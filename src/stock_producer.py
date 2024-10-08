import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
from kafka import KafkaProducer
import json
import pytz
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def fetch_stock_data(ticker, interval, period):
    """Fetch historical market data for a given ticker."""
    try:
        stock = yf.Ticker(ticker)
        end_time = datetime.now(pytz.timezone('US/Eastern'))
        start_time = end_time - timedelta(days=180)
        
        data = stock.history(start=start_time, end=end_time, interval=interval)
        
        if data.empty:
            logging.warning(f"No data retrieved for {ticker}")
        else:
            logging.info(f"Successfully fetched data for {ticker}: {len(data)} records")
        
        return data
    except Exception as e:
        logging.error(f"Error fetching stock data: {e}")
        return pd.DataFrame()

def send_to_kafka(data, producer, topic):
    """Send data to a Kafka topic."""
    if not data.empty:
        data['Time_Zone'] = 'US/Eastern'
        data = data.reset_index()
        data['Datetime'] = data['Datetime'].astype(str)
        
        earliest_record = data.loc[data['Datetime'].idxmin()]
        message = earliest_record.to_json()
        
        try:
            producer.send(topic, value=message.encode('utf-8'))
            logging.info(f"Data sent to Kafka topic: {topic}")
            logging.info(f"Sent data: {message}")
        except Exception as e:
            logging.error(f"Error sending data to Kafka: {e}")
    else:
        logging.warning("No data to send.")

def main():
    ticker = "TSLA"
    interval = "1h"
    kafka_topic = 'stock_data'
    
    bootstrap_servers = os.environ['BOOTSTRAP_SERVERS'].split(',')
    
    try:
        producer = KafkaProducer(bootstrap_servers=bootstrap_servers)
        logging.info("Kafka producer initialized successfully")
    except Exception as e:
        logging.error(f"Failed to initialize Kafka producer: {e}")
        return

    try:
        while True:
            sleep_time = 10
            logging.info(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)

            data = fetch_stock_data(ticker, interval, "6mo")
            send_to_kafka(data, producer, kafka_topic)
    except KeyboardInterrupt:
        logging.info("Producer stopped by user")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        producer.close()
        logging.info("Kafka producer closed")

if __name__ == "__main__":
    main()
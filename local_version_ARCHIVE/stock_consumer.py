from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import os
import logging

last_row = None

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    # Suppress specific Kafka warnings
    logging.getLogger("org.apache.spark").setLevel(logging.ERROR)
    
def process_batch(df, epoch_id):
    """
    Process each batch of data using Spark SQL.

    Args:
        df (DataFrame): The dataframe containing the batch data.
        epoch_id (int): The epoch ID of the batch.
    """
    global last_row
    logging.info(f"Processing batch {epoch_id}")
    
    if df.rdd.isEmpty():
        logging.error(f"Batch {epoch_id} is empty. No data to process.")
        return
    
    # Create a temporary view for Spark SQL
    df.createOrReplaceTempView("stock_data")
    
    # Deduplicate data based on the timestamp using Spark SQL
    deduplicated_df = df.sparkSession.sql("""
        SELECT DISTINCT * 
        FROM stock_data 
        ORDER BY Datetime
    """)
    
    if deduplicated_df.rdd.isEmpty():
        logging.error(f"Batch {epoch_id} contains only duplicate data. Nothing to append.")
        return
    
    output_path = "stock_data_output.csv"
    file_exists = os.path.isfile(output_path)
    
    try:
        pandas_df = deduplicated_df.toPandas()
        if not pandas_df.empty:
            new_last_row = pandas_df.iloc[-1].to_dict()
            if last_row == new_last_row:
                logging.error(f"Batch {epoch_id} contains the same data as the last row. Not appending.")
            else:
                pandas_df.to_csv(
                    output_path, 
                    mode='a', 
                    header=not file_exists, 
                    index=False
                )
                last_row = new_last_row
                logging.info(f"Batch {epoch_id} appended to {output_path}")
    except Exception as e:
        logging.error(f"Error appending batch {epoch_id} to {output_path}: {e}")

def main():
    """
    Main function to set up Spark session and start streaming data processing.
    """
    setup_logging()
    
    try:
        spark = SparkSession.builder \
            .appName("StockDataStreaming") \
            .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2") \
            .getOrCreate()
    except Exception as e:
        logging.error(f"Error creating Spark session: {e}")
        return

    schema = StructType([
        StructField("Open", DoubleType()),
        StructField("High", DoubleType()),
        StructField("Low", DoubleType()),
        StructField("Close", DoubleType()),
        StructField("Volume", DoubleType()),
        StructField("Time_Zone", StringType()),
        StructField("Datetime", TimestampType())
    ])

    try:
        df = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "localhost:9092") \
            .option("subscribe", "stock_data") \
            .option("startingOffsets", "earliest") \
            .load()
    except Exception as e:
        logging.error(f"Error reading from Kafka: {e}")
        return

    parsed_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")
    parsed_df = parsed_df.withColumn("Datetime", to_timestamp("Datetime"))

    filtered_df = parsed_df.filter(
        (col("Open").isNotNull()) & 
        (col("High").isNotNull()) & 
        (col("Low").isNotNull()) & 
        (col("Close").isNotNull()) & 
        (col("Volume").isNotNull()) & 
        (col("Datetime").isNotNull())
    )

    query = filtered_df.writeStream \
        .outputMode("append") \
        .foreachBatch(process_batch) \
        .trigger(processingTime='10 seconds') \
        .start()

    try:
        query.awaitTermination()
    except KeyboardInterrupt:
        logging.error("User stopped the program")
    except Exception as e:
        logging.error(f"Error during stream processing: {e}")

if __name__ == "__main__":
    main()
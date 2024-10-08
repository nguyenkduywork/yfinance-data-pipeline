from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, to_timestamp
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
import os
import logging

def setup_logging():
    """Set up logging configuration."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logging.getLogger("org.apache.spark").setLevel(logging.ERROR)

def process_batch(df, epoch_id):
    """Process each batch of data using Spark SQL."""
    logging.info(f"Processing batch {epoch_id}")
    
    if df.rdd.isEmpty():
        logging.error(f"Batch {epoch_id} is empty. No data to process.")
        return
    
    df.createOrReplaceTempView("stock_data")
    
    deduplicated_df = df.sparkSession.sql("""
        SELECT DISTINCT * 
        FROM stock_data 
        ORDER BY Datetime
    """)
    
    if deduplicated_df.rdd.isEmpty():
        logging.error(f"Batch {epoch_id} contains only duplicate data. Nothing to append.")
        return
    
    output_path = "s3://demo-bucket/stock_data_output.csv"
    
    try:
        deduplicated_df.write.mode("append").csv(output_path)
        logging.info(f"Batch {epoch_id} appended to {output_path}")
    except Exception as e:
        logging.error(f"Error appending batch {epoch_id} to {output_path}: {e}")

def main():
    """Main function to set up Spark session and start streaming data processing."""
    setup_logging()
    
    spark = SparkSession.builder \
        .appName("EMRServerlessStockDataStreaming") \
        .getOrCreate()

    schema = StructType([
        StructField("Open", DoubleType()),
        StructField("High", DoubleType()),
        StructField("Low", DoubleType()),
        StructField("Close", DoubleType()),
        StructField("Volume", DoubleType()),
        StructField("Time_Zone", StringType()),
        StructField("Datetime", TimestampType())
    ])

    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", os.environ['BOOTSTRAP_SERVERS']) \
        .option("subscribe", "stock_data") \
        .option("startingOffsets", "earliest") \
        .load()

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

    query.awaitTermination()

if __name__ == "__main__":
    main()
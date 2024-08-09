[Setting up JDK, Hadoop WinUtils, Spark binaries and environment variables on Windows/x64 System](https://app.tango.us/app/workflow/Setting-up-JDK--Hadoop-WinUtils--Spark-binaries-and-environment-variables-on-Windows-x64-System-ce23bd438117424c87009b2ac1fc82bd)

[Download Terraform on Windows](https://app.tango.us/app/workflow/Downloading-Terraform-on-Windows--A-Quick-Tutorial-63634416f09348c4857f64e3804235a2)

[Download and Configure Apache Kafka on Windows/x64 System](https://app.tango.us/app/workflow/Download-and-Configure-Apache-Kafka-on-Windows-x64-System-474eb2506acd494ebd5c94686ea610c2)

Install Kafka:

Download Kafka from the official website
Extract it to a directory, e.g., C:\kafka


Start Zookeeper and Kafka:

Open a command prompt and navigate to the Kafka directory
Start Zookeeper: %KAFKA_HOME%\bin\windows\zookeeper-server-start.bat %KAFKA_HOME%\config\zookeeper.properties
Open another command prompt and start Kafka: .%KAFKA_HOME%\bin\windows\kafka-server-start.bat %KAFKA_HOME%\config\server.properties


Create a Kafka topic:

Open another command prompt and run: %KAFKA_HOME%\bin\windows\kafka-topics.bat --create --topic stock_data --bootstrap-server localhost:9092



Install required Python libraries:

Run: pip install kafka-python pyspark yfinance pandas pytz


Run the producer:

Save the producer code to a file (e.g., stock_producer.py)
Run: python stock_producer.py


Run the consumer:

Save the consumer code to a file (e.g., stock_consumer.py)
Run: spark-submit --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.1.2 stock_consumer.py
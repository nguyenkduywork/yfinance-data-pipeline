# Stock Data Streaming with AWS EMR Serverless and Amazon MSK

This project demonstrates a real-time stock data streaming solution using AWS EMR Serverless for data processing and Amazon MSK (Managed Streaming for Apache Kafka) for message streaming. The infrastructure is provisioned using Terraform, and the data processing is implemented using PySpark.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Components](#components)
4. [Prerequisites](#prerequisites)
5. [Setup Instructions](#setup-instructions)
6. [Usage](#usage)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Cleaning Up](#cleaning-up)


## Project Overview

This project sets up a data pipeline that fetches real-time stock data, streams it through Kafka, processes it using Spark on EMR Serverless, and stores the results in Amazon S3. It showcases how to use modern cloud services for building scalable, real-time data processing solutions.

## Architecture

The project uses the following AWS services:

- Amazon MSK (Managed Streaming for Apache Kafka) for data streaming
- AWS EMR Serverless for running Spark jobs
- Amazon S3 for storing processed data
- Amazon EC2 for a bastion host to interact with the Kafka cluster
- Amazon VPC for networking

## Components

1. **Terraform Configuration (`main.tf`)**: Defines the AWS infrastructure, including the EMR Serverless application, MSK cluster, VPC, subnets, security groups, and EC2 bastion host.

2. **Stock Data Producer (`stock_producer.py`)**: A Python script that fetches stock data from Yahoo Finance and sends it to a Kafka topic.

3. **Stock Data Consumer (`stock_consumer.py`)**: A PySpark application that reads data from Kafka, processes it, and writes the results to S3.

4. **Bastion Host**: An EC2 instance that allows secure access to the Kafka cluster within the VPC.

## Prerequisites

- AWS Account with appropriate permissions
- Terraform installed (version 0.12 or later)
- Python 3.7 or later
- AWS CLI configured with your credentials

## Setup Instructions

1. Clone this repository to your local machine.

2. Navigate to the project directory and initialize Terraform:
   ```
   terraform init
   ```

3. Review and modify the `variables.tf` file to customize any default values.

4. Apply the Terraform configuration:
   ```
   terraform apply
   ```

5. Once the infrastructure is provisioned, note the following outputs:
   - MSK Bootstrap Servers
   - S3 bucket name
   - Bastion host public IP

6. Upload the `stock_producer.py` and `stock_consumer.py` scripts to the S3 bucket:
   ```
   aws s3 cp stock_producer.py s3://demo-bucket/code/
   aws s3 cp stock_consumer.py s3://demo-bucket/code/
   ```

7. SSH into the bastion host:
   ```
   ssh -i cert.pem ec2-user@<bastion-host-public-ip>
   ```

8. From the bastion host, run the stock data producer:
   ```
   python3 stock_producer.py
   ```

9. Submit the Spark job to EMR Serverless:
   ```
   aws emr-serverless start-job-run \
     --application-id <emr-serverless-application-id> \
     --execution-role-arn <emr-serverless-role-arn> \
     --job-driver '{
       "sparkSubmit": {
         "entryPoint": "s3://demo-bucket/code/stock_consumer.py",
         "sparkSubmitParameters": "--conf spark.executor.cores=1 --conf spark.executor.memory=4g --conf spark.driver.cores=1 --conf spark.driver.memory=4g --conf spark.executor.instances=1"
       }
     }' \
     --configuration-overrides '{
       "monitoringConfiguration": {
         "s3MonitoringConfiguration": {
           "logUri": "s3://demo-bucket/logs/"
         }
       }
     }'
   ```

## Usage

Once the setup is complete and both the producer and consumer are running:

1. The stock data producer will continuously fetch data and send it to the Kafka topic.
2. The EMR Serverless application will process the data in micro-batches.
3. Processed data will be stored in the S3 bucket as CSV files.

You can monitor the process through CloudWatch logs and by checking the S3 bucket for output files.

## Monitoring and Logging

- EMR Serverless logs: Available in CloudWatch Logs
- MSK broker logs: Available in CloudWatch Logs
- Producer logs: Available on the bastion host
- Processed data: Check the S3 bucket for output files

## Cleaning Up

To avoid incurring unnecessary charges, remember to destroy the resources when you're done:

1. Stop the EMR Serverless application.
2. Terminate any running EC2 instances.
3. Run `terraform destroy` to remove all created resources.

Note: Make sure to backup any important data before destroying the resources.

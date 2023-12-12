# TwitterTrendData Repository
PySpark and NLP-powered project analyzing historical Twitter data for trending topics based on word frequency and slope.
## Requirements
- Python 3.9
- MongoDB
- PySpark
- PyMongo
- Spacy
- Docker
- AWS S3
## Overview
This repository contains an ETL pipeline designed for Twitter trend analysis. The pipeline consists of three main components:

**1. Extract to MongoDB:**

The script extracts data from a datasource file (twitter-sample, twitter-sample-2) and loads it into a MongoDB collection.
- Usage:
  
  ```
  python 1_extract_to_mongo.py <filename> [-verbose]
  ```
**2. Calculate Trend with PySpark:**

This script utilizes PySpark for Twitter trend analysis. It performs NLP to extract nouns from tweet texts and calculates trending topics over a specified time window. IT outputs results as a CSV file.
- Usage:
  
  ```
  python 2_calculate_trend.py <database> <collection> [-verbose]
  ```
**3. Load to S3:**

The script uploads CSV files (output from trend analysis) to an AWS S3 bucket for storage and further analysis.
- Usage:
  
  ```
  python 3_load_to_S3.py
  ```
## Docker
Separate Dockerfiles are provided for each script to facilitate containerization and deployment. The docker-compose.yml file is provided for orchestrating the deployment of Docker containers for each script.
## Configuration
Configuration details such as MongoDB server information are stored in the config.py and config_hidden.ini files.


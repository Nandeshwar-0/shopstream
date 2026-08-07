# ShopStream Data Engineering Pipeline

## Overview
ShopStream is a synthetic e-commerce data engineering pipeline demonstrating a complete end-to-end Medallion architecture (Bronze -> Silver -> Gold). The pipeline incrementally extracts data from a PostgreSQL OLTP database, stores it in an S3-compatible Data Lake (MinIO), transforms and aggregates the data using PySpark, enforces Data Quality checks, and is orchestrated by Apache Airflow.

## Architecture & Technology Stack
* **Source Database:** PostgreSQL (OLTP schema for customers, orders, inventory, etc.)
* **Data Lake:** MinIO (S3-Compatible Object Storage)
* **Data Processing:** PySpark
* **Data Formats:** Parquet
* **Orchestration:** Apache Airflow
* **Language:** Python 3.10+

## The Medallion Pipeline Phases
1. **Phase 1: Incremental Extraction** (`ingestion/extractor.py`)
   - Reads a `etl_watermarks` table to determine the last `updated_at` timestamp.
   - Extracts only new and updated rows from PostgreSQL tables using Pandas.
2. **Phase 2: Bronze Layer Ingestion** (`ingestion/minio_client.py`)
   - Uploads the extracted records directly into MinIO (`s3://shopstream-lake/bronze/`) as `.parquet` files via an in-memory buffer.
3. **Phase 3: Silver Layer Transformation** (`spark/silver_transformer.py`)
   - Reads raw Bronze Parquet files using PySpark.
   - Deduplicates records based on `updated_at` (keeping only the latest row per primary key).
   - Writes clean, schema-enforced data to the Silver layer (`s3://shopstream-lake/silver/`).
4. **Phase 4: Data Quality Observability** (`spark/data_quality.py`)
   - Runs assertions on the Silver layer (e.g., checks for NULL primary keys and duplicate records).
   - Fails the Airflow pipeline defensively if data is corrupted.
5. **Phase 5: Gold Layer Aggregation** (`spark/gold_aggregator.py`)
   - Reads pristine Silver data.
   - Joins `orders`, `order_items`, and `products` to denormalize the data.
   - Aggregates units sold and total revenue per product, creating business-ready metrics for BI dashboards.
6. **Orchestration** (`airflow/dags/shopstream_dag.py`)
   - A daily DAG that chains the steps: Extract -> Transform -> Check Quality -> Aggregate.

## Local Setup & Usage

### 1. Requirements
Ensure you have Docker and Java 17 installed (required for PySpark).
```bash
sudo apt install openjdk-17-jdk
```

### 2. Python Environment
Create a virtual environment and install dependencies:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Infrastructure
Spin up the backend services (PostgreSQL and MinIO):
```bash
docker-compose up -d
```

### 4. Running the Pipeline Manually
You can run the steps manually instead of using Airflow:

1. Generate dummy data:
```bash
PYTHONPATH=. python -m data_generator.run_generator
```
2. Run extraction (Postgres to Bronze):
```bash
PYTHONPATH=. python ingestion/run_extraction.py
```
3. Run Silver transformation:
```bash
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PYTHONPATH=. python -m spark.silver_transformer
```
4. Check Data Quality:
```bash
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PYTHONPATH=. python -m spark.data_quality
```
5. Run Gold Aggregation:
```bash
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 PYTHONPATH=. python -m spark.gold_aggregator
```

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

# Default arguments applied to all tasks
default_args = {
    'owner': 'data_engineering_team',
    'depends_on_past': False,
    'email_on_failure': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

with DAG(
    'shopstream_daily_etl',
    default_args=default_args,
    description='Incremental ETL from Postgres to MinIO (Bronze -> Silver -> Gold)',
    schedule_interval=timedelta(days=1), # Run daily at midnight
    start_date=datetime(2026, 8, 1),
    catchup=False,
    tags=['shopstream', 'etl'],
) as dag:

    # Task 1: Extract from Postgres to Bronze
    extract_to_bronze = BashOperator(
        task_id='extract_to_bronze',
        bash_command='cd /opt/airflow && PYTHONPATH=. python ingestion/run_extraction.py',
    )

    # Task 2: Transform Bronze to Silver
    transform_to_silver = BashOperator(
        task_id='transform_to_silver',
        bash_command='cd /opt/airflow && PYTHONPATH=. python -m spark.silver_transformer',
    )

    # Task 3: Data Quality Check on Silver
    check_silver_quality = BashOperator(
        task_id='check_silver_quality',
        bash_command='cd /opt/airflow && PYTHONPATH=. python -m spark.data_quality',
    )

    # Task 4: Aggregate Silver to Gold
    aggregate_to_gold = BashOperator(
        task_id='aggregate_to_gold',
        bash_command='cd /opt/airflow && PYTHONPATH=. python -m spark.gold_aggregator',
    )

    # Define the dependency graph!
    extract_to_bronze >> transform_to_silver >> check_silver_quality >> aggregate_to_gold

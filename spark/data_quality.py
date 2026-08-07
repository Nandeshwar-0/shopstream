from pyspark.sql.functions import col
from spark.spark_session import get_spark_session
import sys

def check_data_quality():
    print("Running Data Quality Checks on Silver Layer...")
    spark = get_spark_session("DataQuality")
    bucket = "s3a://shopstream-lake"
    
    try:
        # Read Silver orders
        orders_df = spark.read.parquet(f"{bucket}/silver/orders/")
        
        # Check 1: No NULL order IDs
        null_count = orders_df.filter(col("order_id").isNull()).count()
        if null_count > 0:
            print(f"❌ DATA QUALITY ALERT: Found {null_count} rows with NULL order_id!")
            sys.exit(1) # Exit with '1' so Airflow knows the task failed!
            
        # Check 2: Uniqueness of Order IDs (No duplicates)
        total_orders = orders_df.count()
        distinct_orders = orders_df.select("order_id").distinct().count()
        if total_orders != distinct_orders:
            print(f"❌ DATA QUALITY ALERT: Found duplicates! Total rows: {total_orders}, Unique IDs: {distinct_orders}")
            sys.exit(1)
            
        print("✅ All Data Quality checks passed successfully! Your Silver data is pristine.")
        
    except Exception as e:
        print(f"Failed to run Data Quality checks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    check_data_quality()

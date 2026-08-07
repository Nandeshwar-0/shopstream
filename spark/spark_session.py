from pyspark.sql import SparkSession
from ingestion.config import settings

def get_spark_session(app_name: str = "ShopStream") -> SparkSession:
    """
    Creates a SparkSession configured to connect to our local MinIO instance.
    """
    spark = SparkSession.builder \
        .appName(app_name) \
        .config("spark.jars.packages", "org.apache.hadoop:hadoop-aws:3.3.4,com.amazonaws:aws-java-sdk-bundle:1.12.262") \
        .config("spark.hadoop.fs.s3a.endpoint", f"http://{settings.minio_endpoint}") \
        .config("spark.hadoop.fs.s3a.access.key", settings.minio_access_key) \
        .config("spark.hadoop.fs.s3a.secret.key", settings.minio_secret_key) \
        .config("spark.hadoop.fs.s3a.path.style.access", "true") \
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem").getOrCreate()
        # .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
        # .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog") \
        
    return spark

from pyspark.sql import DataFrame
from pyspark.sql.window import Window
from pyspark.sql.functions import col, row_number

from spark.spark_session import get_spark_session

class SilverTransformer:
    def __init__(self):
        self.spark = get_spark_session("BronzeToSilver")
        self.bucket = "s3a://shopstream-lake"
        
    def deduplicate(self, df: DataFrame, primary_key: str, order_by_col: str = "updated_at") -> DataFrame:
        """
        Keeps only the latest row for each primary key based on the order_by_col.
        """
        window_spec = Window.partitionBy(primary_key).orderBy(col(order_by_col).desc())
        
        # Rank the rows and keep only the first one (the latest)
        deduped_df = df.withColumn("row_num", row_number().over(window_spec)) \
                       .filter(col("row_num") == 1) \
                       .drop("row_num")
                       
        return deduped_df

    def process_table(self, table_name: str, primary_key: str):
        print(f"Processing {table_name}...")
        
        bronze_path = f"{self.bucket}/bronze/{table_name}/"
        silver_path = f"{self.bucket}/silver/{table_name}/"
        
        try:
            # 1. Read Bronze data
            df = self.spark.read.parquet(bronze_path)
            
            # 2. Clean & Deduplicate
            clean_df = self.deduplicate(df, primary_key)
            
            # 3. Write to Silver (Overwrite mode for now, though MERGE is used in advanced setups)
            clean_df.write.mode("overwrite").parquet(silver_path)
            print(f"Successfully processed and saved {table_name} to Silver layer.")
            
        except Exception as e:
            print(f"Failed to process {table_name}: {e}")

if __name__ == "__main__":
    transformer = SilverTransformer()
    
    # Process our core tables with their respective primary keys
    tables_to_process = {
        "customers": "customer_id",
        "products": "product_id",
        "orders": "order_id",
        "order_items": "order_item_id"
    }
    
    for table, pk in tables_to_process.items():
        transformer.process_table(table, pk)

from pyspark.sql.functions import sum as _sum, col
from spark.spark_session import get_spark_session

class GoldAggregator:
    def __init__(self):
        self.spark = get_spark_session("SilverToGold")
        self.bucket = "s3a://shopstream-lake"
        
    def generate_product_performance_metrics(self):
        print("Generating Product Performance Metrics...")
        
        try:
            # 1. Read from Silver
            orders_df = self.spark.read.parquet(f"{self.bucket}/silver/orders/")
            items_df = self.spark.read.parquet(f"{self.bucket}/silver/order_items/")
            products_df = self.spark.read.parquet(f"{self.bucket}/silver/products/")

            print(f"Total orders in Silver: {orders_df.count()}")
            print(f"Total items in Silver: {items_df.count()}") 
            print(f"Total products in Silver: {products_df.count()}")
            
            # Filter for completed orders
            completed_orders = orders_df.filter(col("order_status") == "DELIVERED")
            print(f"Total DELIVERED orders: {completed_orders.count()}")
            
            # 2. Join & Aggregate
            valid_items = items_df.join(completed_orders, "order_id", "inner")
            
            product_metrics = valid_items.groupBy("product_id").agg(
                _sum("quantity").alias("total_units_sold"),
                _sum("total_price").alias("total_revenue")
            )
            
            final_gold_df = product_metrics.join(products_df, "product_id", "inner") \
                                           .select("product_id", "name", "total_units_sold", "total_revenue") \
                                           .orderBy(col("total_revenue").desc())
                                           
            # 3. Write to Gold
            gold_path = f"{self.bucket}/gold/product_performance/"
            final_gold_df.write.mode("overwrite").parquet(gold_path)
            
            print("Successfully generated Product Performance Gold dataset!")
            final_gold_df.show(5) # Preview the top 5 products
            
        except Exception as e:
            print(f"Failed to generate gold metrics: {e}")

if __name__ == "__main__":
    aggregator = GoldAggregator()
    aggregator.generate_product_performance_metrics()

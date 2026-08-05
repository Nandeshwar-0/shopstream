from __future__ import annotations
import os
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path

from ingestion.config import settings
from ingestion.watermark import WatermarkManager
from data_generator.db import PostgresClient

class IncrementalExtractor:
    def __init__(self, table_name: str, date_column: str = "updated_at"):
        self.table_name = table_name
        self.date_column = date_column
        self.watermark_mgr = WatermarkManager()
        
        # Determine the table's directory in bronze layer
        self.bronze_table_dir = Path(settings.bronze_dir) / table_name
        self.bronze_table_dir.mkdir(parents=True, exist_ok=True)

    def extract(self) -> int:
        """
        Executes the incremental extraction to Parquet.
        Returns the number of rows extracted.
        """
        # 1. Read Watermark
        last_watermark = self.watermark_mgr.get_watermark(self.table_name)
        print(f"[{self.table_name}] Extracting data modified after {last_watermark}")

        # 2. Extract Data
        # We subtract a 1-minute buffer to catch in-flight transactions (overlap)
        query = f"""
            SELECT * 
            FROM {self.table_name} 
            WHERE {self.date_column} >= %s 
            ORDER BY {self.date_column} ASC
        """
        
        # Read from Postgres using our context manager and create DataFrame
        with PostgresClient() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (last_watermark,))
                rows = cur.fetchall()
                # If there are no rows, fetchall() returns empty list
                
        df = pd.DataFrame(rows)
        
        row_count = len(df)
        if row_count == 0:
            print(f"[{self.table_name}] No new records to extract.")
            return 0

        # 3. Save to Bronze (Parquet)
        # Generate a unique filename based on current time
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filename = f"{self.table_name}_{timestamp_str}.parquet"
        filepath = self.bronze_table_dir / filename
        
        # Write to parquet, preserving types
        df.to_parquet(filepath, engine="pyarrow", index=False)
        print(f"[{self.table_name}] Extracted {row_count} rows to {filepath}")

        # 4. Update Watermark
        # Find the max updated_at in the extracted dataset
        max_timestamp = df[self.date_column].max()
        # Convert numpy datetime64 to python datetime if needed
        if isinstance(max_timestamp, pd.Timestamp):
            max_timestamp = max_timestamp.to_pydatetime()
            
        self.watermark_mgr.update_watermark(self.table_name, max_timestamp)
        print(f"[{self.table_name}] Updated watermark to {max_timestamp}")
        
        return row_count


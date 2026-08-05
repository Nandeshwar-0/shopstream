from __future__ import annotations
from datetime import datetime

# We can reuse the PostgresClient from data_generator since it's already robust
# In a real project, we might refactor db.py to a common utils package.
from data_generator.db import PostgresClient

class WatermarkManager:
    """Manages high-watermarks for incremental ETL using PostgreSQL."""

    def get_watermark(self, table_name: str) -> datetime:
        """Fetch the current watermark for a table."""
        sql = "SELECT watermark_value FROM etl_watermarks WHERE table_name = %s"
        with PostgresClient() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (table_name,))
                row = cur.fetchone()
                if row:
                    return row["watermark_value"]
                
                # Default for first run: 1970-01-01
                return datetime(1970, 1, 1)

    def update_watermark(self, table_name: str, new_watermark: datetime) -> None:
        """Update the watermark after a successful extraction."""
        sql = """
            INSERT INTO etl_watermarks (table_name, watermark_value, last_run)
            VALUES (%s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (table_name) 
            DO UPDATE SET 
                watermark_value = EXCLUDED.watermark_value,
                last_run = EXCLUDED.last_run
        """
        with PostgresClient() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (table_name, new_watermark))


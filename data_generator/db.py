from __future__ import annotations
from contextlib import contextmanager
from psycopg import connect
from psycopg.rows import dict_row

from .config import settings

class PostgresClient:
    def __init__(self):
        self._conn = None

    def __enter__(self):
        self._conn = connect(
            host=settings.postgres_host,
            port=settings.postgres_port,
            dbname=settings.postgres_db,
            user=settings.postgres_user,
            password=settings.postgres_password,
            autocommit=False,
            row_factory=dict_row,
        )
        return self._conn

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            self._conn.rollback()
        else:
            self._conn.commit()
        self._conn.close()

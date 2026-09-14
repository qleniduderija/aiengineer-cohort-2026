import os
from pathlib import Path

import psycopg
from pgvector.psycopg import register_vector

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def get_connection() -> psycopg.Connection:
    conn = psycopg.connect(os.environ["DATABASE_URL"])
    conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
    register_vector(conn)
    return conn


def init_schema(conn: psycopg.Connection) -> None:
    conn.execute(SCHEMA_PATH.read_text())
    conn.commit()

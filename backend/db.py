"""
Optional query/answer logging to PostgreSQL — feeds Week 7's analytics.

Designed to fail SOFTLY: if Postgres isn't running yet, the API still works,
it just skips logging (with a printed warning) instead of crashing requests.
This lets you build the backend now and wire up the database whenever you
get to it, without blocking progress.
"""

import os
import datetime

DB_ENABLED = True  # flip to False to disable logging entirely without touching other code

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "dbname": "biat_rag",
    "user": "postgres",
    "password": "postgres",
}

_connection = None


def get_connection():
    global _connection
    if not DB_ENABLED:
        return None
    if _connection is not None:
        return _connection
    try:
        import psycopg2
        _connection = psycopg2.connect(**DB_CONFIG)
        _ensure_table(_connection)
        return _connection
    except Exception as e:
        print(f"[db] Could not connect to Postgres, logging disabled: {e}")
        return None


def _ensure_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS query_log (
                id SERIAL PRIMARY KEY,
                question TEXT NOT NULL,
                answer TEXT NOT NULL,
                matched BOOLEAN NOT NULL,
                sources TEXT,
                created_at TIMESTAMP NOT NULL
            );
        """)
        conn.commit()


def log_query(question: str, answer: str, matched: bool, sources: list[str]):
    conn = get_connection()
    if conn is None:
        return  # logging disabled or unavailable — silently skip

    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO query_log (question, answer, matched, sources, created_at)
                   VALUES (%s, %s, %s, %s, %s)""",
                (question, answer, matched, ", ".join(sources), datetime.datetime.now()),
            )
            conn.commit()
    except Exception as e:
        print(f"[db] Failed to log query: {e}")

import os

from contextlib import contextmanager

import psycopg2
import psycopg2.pool

from psycopg2.extras import RealDictCursor

from dotenv import load_dotenv


load_dotenv()


def _create_pool():
    return psycopg2.pool.ThreadedConnectionPool(
        1,
        10,
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


connection_pool = None

try:

    connection_pool = _create_pool()

    print("✅ PostgreSQL connection pool ready")


except Exception as e:

    print("❌ Database Connection Failed")

    print(e)


@contextmanager
def get_cursor():
    """
    Borrow a connection from the pool, yield a RealDictCursor,
    commit on success, roll back on error. If the connection
    itself turns out to be broken, it is discarded from the pool
    instead of being returned, so the next request gets a fresh
    one automatically.
    """

    global connection_pool

    if connection_pool is None:
        connection_pool = _create_pool()

    conn = connection_pool.getconn()
    broken = False

    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        yield cursor
        conn.commit()

    except (psycopg2.OperationalError, psycopg2.InterfaceError):
        broken = True
        raise

    except Exception:
        conn.rollback()
        raise

    finally:
        if broken:
            connection_pool.putconn(conn, close=True)
        else:
            connection_pool.putconn(conn)


def ensure_chat_schema():

    with get_cursor() as cursor:

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id SERIAL PRIMARY KEY,
                title TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )

        cursor.execute(
            """
            ALTER TABLE chat_history
            ADD COLUMN IF NOT EXISTS session_id INTEGER
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS collections (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
            """
        )

        cursor.execute(
            """
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS collection_id INTEGER
            """
        )

        cursor.execute(
            """
            ALTER TABLE documents
            ADD COLUMN IF NOT EXISTS processed_chunks INTEGER DEFAULT 0
            """
        )

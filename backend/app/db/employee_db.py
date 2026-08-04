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
        database=os.getenv("EMPLOYEE_DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD")
    )


connection_pool = None

try:

    connection_pool = _create_pool()

    print("✅ Employee PostgreSQL connection pool ready")


except Exception as e:

    print("❌ Employee Database Connection Failed")

    print(e)


@contextmanager
def get_employee_cursor():
    """
    Borrow a connection from the employee-database pool, yield a
    RealDictCursor, roll back on error (this pool is read-only from the
    app's side, but rollback keeps behavior symmetric with get_cursor()).
    If the connection itself turns out to be broken, it is discarded from
    the pool instead of being returned.
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

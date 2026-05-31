# hms_web/database/db.py
import mysql.connector
from mysql.connector import Error
from config import Config


def get_connection():
    """Return a new MySQL connection using Config values."""
    try:
        conn = mysql.connector.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            autocommit=False,
            charset="utf8mb4",
        )
        return conn
    except Error as e:
        raise ConnectionError(f"MySQL connection failed: {e}")


def execute_query(query: str, params=None, fetch=False):
    """
    Execute a single query.
    - fetch=True  → returns list of dicts
    - fetch=False → returns (lastrowid, rowcount)
    Opens and closes its own connection so routes stay stateless.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        if fetch:
            result = cursor.fetchall()
            return result
        conn.commit()
        return cursor.lastrowid, cursor.rowcount
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def execute_many(query: str, data_list: list):
    """Execute a query for a list of parameter tuples (bulk insert/update)."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(query, data_list)
        conn.commit()
        return cursor.rowcount
    except Error as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()
import sqlite3
import os
from contextlib import contextmanager

DATABASE_PATH = os.path.join('data', 'students.db')

def get_db():
    """Get database connection."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access
    return conn

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = get_db()
    try:
        yield conn
    finally:
        conn.close()


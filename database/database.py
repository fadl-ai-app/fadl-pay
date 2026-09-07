
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "fadl_pay.db"


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS merchants (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            merchant_reference TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_reference TEXT UNIQUE NOT NULL,
            name TEXT,
            email TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_reference TEXT UNIQUE NOT NULL,
            merchant_reference TEXT NOT NULL,
            customer_reference TEXT,
            amount INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'SDG',
            status TEXT NOT NULL DEFAULT 'pending',
            payment_method TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_reference TEXT NOT NULL,
            event_type TEXT NOT NULL,
            event_data TEXT,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DB_PATH}")

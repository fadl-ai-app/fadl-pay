
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


    # --------------------------------------------------------
    # Missing schemas restored from verified Reference DB
    # --------------------------------------------------------

    cursor.execute("CREATE TABLE IF NOT EXISTS api_keys (\n            id INTEGER PRIMARY KEY AUTOINCREMENT,\n            merchant_reference TEXT NOT NULL,\n            key_hash TEXT UNIQUE NOT NULL,\n            status TEXT NOT NULL DEFAULT 'active',\n            created_at TEXT NOT NULL\n        )")

    cursor.execute("CREATE TABLE IF NOT EXISTS countries (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    country_code TEXT UNIQUE NOT NULL,\n    country_name TEXT NOT NULL,\n    region TEXT,\n    status TEXT NOT NULL DEFAULT 'active',\n    created_at TEXT NOT NULL\n)")

    cursor.execute("CREATE TABLE IF NOT EXISTS currencies (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    currency_code TEXT UNIQUE NOT NULL,\n    currency_name TEXT NOT NULL,\n    symbol TEXT,\n    decimal_places INTEGER DEFAULT 2,\n    status TEXT NOT NULL DEFAULT 'active',\n    created_at TEXT NOT NULL\n)")

    cursor.execute('CREATE TABLE IF NOT EXISTS idempotency_keys (\n        id INTEGER PRIMARY KEY AUTOINCREMENT,\n        merchant_reference TEXT NOT NULL,\n        idempotency_key TEXT NOT NULL,\n        transaction_reference TEXT NOT NULL,\n        request_hash TEXT NOT NULL,\n        created_at TEXT NOT NULL,\n        UNIQUE (\n            merchant_reference,\n            idempotency_key\n        )\n    )')

    cursor.execute("CREATE TABLE IF NOT EXISTS ledger_entries (\n\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n\n    transaction_reference TEXT NOT NULL,\n\n    merchant_reference TEXT NOT NULL,\n\n    entry_type TEXT NOT NULL,\n\n    amount INTEGER NOT NULL,\n\n    currency TEXT NOT NULL DEFAULT 'SDG',\n\n    description TEXT,\n\n    created_at TEXT NOT NULL\n\n)")

    cursor.execute('CREATE TABLE IF NOT EXISTS merchant_countries (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    merchant_reference TEXT NOT NULL,\n    country_code TEXT NOT NULL,\n    created_at TEXT NOT NULL\n)')

    cursor.execute('CREATE TABLE IF NOT EXISTS supported_currencies (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    merchant_reference TEXT NOT NULL,\n    currency_code TEXT NOT NULL,\n    created_at TEXT NOT NULL\n)')

    cursor.execute("CREATE TABLE IF NOT EXISTS webhook_deliveries (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    event_id INTEGER NOT NULL,\n    transaction_reference TEXT NOT NULL,\n    webhook_url TEXT NOT NULL,\n    payload TEXT NOT NULL,\n    signature TEXT NOT NULL,\n    status TEXT NOT NULL DEFAULT 'pending',\n    attempts INTEGER NOT NULL DEFAULT 0,\n    response_status INTEGER,\n    error_message TEXT,\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL\n, webhook_endpoint_id INTEGER)")

    cursor.execute("CREATE TABLE IF NOT EXISTS webhook_endpoints (\n    id INTEGER PRIMARY KEY AUTOINCREMENT,\n    merchant_reference TEXT NOT NULL,\n    webhook_url TEXT NOT NULL,\n    webhook_secret TEXT NOT NULL,\n    status TEXT NOT NULL DEFAULT 'active',\n    created_at TEXT NOT NULL,\n    updated_at TEXT NOT NULL\n)")

    connection.commit()
    connection.close()


if __name__ == "__main__":
    initialize_database()
    print(f"Database initialized: {DB_PATH}")

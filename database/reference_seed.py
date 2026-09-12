# ============================================================
# FADL PAY — REFERENCE DATA SEED
# ============================================================

from pathlib import Path
from datetime import datetime, timezone
import json


SEED_FILE = Path(__file__).resolve().parent / "reference_data.json"


def seed_reference_data(connection):
    """
    Idempotently seed FADL PAY reference/master data.

    Seeds ONLY:
      - countries
      - currencies
      - merchants
      - merchant_countries
      - supported_currencies

    Does NOT seed:
      - transactions
      - ledger entries
      - API keys
      - webhook data
      - customers
      - historical events
    """

    if not SEED_FILE.exists():
        raise FileNotFoundError(
            f"Reference seed file not found: {SEED_FILE}"
        )

    data = json.loads(
        SEED_FILE.read_text(encoding="utf-8")
    )

    now = datetime.now(timezone.utc).isoformat()

    cursor = connection.cursor()

    # --------------------------------------------------------
    # Countries
    # --------------------------------------------------------
    for row in data["countries"]:
        cursor.execute(
            """
            INSERT OR IGNORE INTO countries (
                country_code,
                country_name,
                region,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row["country_code"],
                row["country_name"],
                row.get("region"),
                row.get("status", "active"),
                row.get("created_at") or now,
            ),
        )

    # --------------------------------------------------------
    # Currencies
    # --------------------------------------------------------
    for row in data["currencies"]:
        cursor.execute(
            """
            INSERT OR IGNORE INTO currencies (
                currency_code,
                currency_name,
                symbol,
                decimal_places,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                row["currency_code"],
                row["currency_name"],
                row.get("symbol"),
                row.get("decimal_places", 2),
                row.get("status", "active"),
                row.get("created_at") or now,
            ),
        )

    # --------------------------------------------------------
    # Merchants
    # --------------------------------------------------------
    for row in data["merchants"]:
        cursor.execute(
            """
            INSERT OR IGNORE INTO merchants (
                merchant_reference,
                name,
                email,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                row["merchant_reference"],
                row["name"],
                row["email"],
                row.get("status", "pending"),
                row.get("created_at") or now,
            ),
        )

    # --------------------------------------------------------
    # Merchant → Countries
    # --------------------------------------------------------
    for row in data["merchant_countries"]:
        cursor.execute(
            """
            INSERT INTO merchant_countries (
                merchant_reference,
                country_code,
                created_at
            )
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM merchant_countries
                WHERE merchant_reference = ?
                  AND country_code = ?
            )
            """,
            (
                row["merchant_reference"],
                row["country_code"],
                row.get("created_at") or now,
                row["merchant_reference"],
                row["country_code"],
            ),
        )

    # --------------------------------------------------------
    # Merchant → Supported Currencies
    # --------------------------------------------------------
    for row in data["supported_currencies"]:
        cursor.execute(
            """
            INSERT INTO supported_currencies (
                merchant_reference,
                currency_code,
                created_at
            )
            SELECT ?, ?, ?
            WHERE NOT EXISTS (
                SELECT 1
                FROM supported_currencies
                WHERE merchant_reference = ?
                  AND currency_code = ?
            )
            """,
            (
                row["merchant_reference"],
                row["currency_code"],
                row.get("created_at") or now,
                row["merchant_reference"],
                row["currency_code"],
            ),
        )

    return {
        "countries": len(data["countries"]),
        "currencies": len(data["currencies"]),
        "merchants": len(data["merchants"]),
        "merchant_countries": len(data["merchant_countries"]),
        "supported_currencies": len(data["supported_currencies"]),
    }

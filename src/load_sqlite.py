
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "processed" / "clean_transactions.csv"
DB_DIR = ROOT / "database"
DB_PATH = DB_DIR / "retail.db"

DB_DIR.mkdir(parents=True, exist_ok=True)

if not CSV_PATH.exists():
    raise FileNotFoundError(f"Cleaned CSV not found: {CSV_PATH}")

if DB_PATH.exists():
    DB_PATH.unlink()

total_rows = 0

with sqlite3.connect(DB_PATH) as conn:
    for chunk in pd.read_csv(CSV_PATH, chunksize=50_000):
        chunk.to_sql(
            "transactions",
            conn,
            if_exists="replace" if total_rows == 0 else "append",
            index=False,
        )
        total_rows += len(chunk)
        print(f"Loaded {total_rows:,} rows")

    # Add indexes to speed up common reporting queries.
    conn.execute(
        "CREATE INDEX idx_transactions_date "
        "ON transactions (InvoiceDate)"
    )
    conn.execute(
        "CREATE INDEX idx_transactions_stock "
        "ON transactions (StockCode)"
    )
    conn.execute(
        "CREATE INDEX idx_transactions_invoice "
        "ON transactions (InvoiceNo)"
    )

    database_rows = conn.execute(
        "SELECT COUNT(*) FROM transactions"
    ).fetchone()[0]

print(f"\nDatabase created: {DB_PATH}")
print(f"CSV rows loaded: {total_rows:,}")
print(f"Database rows verified: {database_rows:,}")

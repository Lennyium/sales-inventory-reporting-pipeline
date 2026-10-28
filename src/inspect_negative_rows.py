
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "retail.db"

query = """
SELECT
    InvoiceNo,
    InvoiceDate,
    StockCode,
    Description,
    Quantity,
    UnitPrice,
    LineAmount,
    is_cancellation_invoice
FROM transactions
WHERE Quantity < 0
  AND is_cancellation_invoice = 0
ORDER BY InvoiceDate
LIMIT 30
"""

with sqlite3.connect(DB_PATH) as conn:
    sample = pd.read_sql_query(query, conn)

    print(sample.to_string(index=False))

    print("\nSummary:")
    summary = pd.read_sql_query("""
        SELECT
            COUNT(*) AS row_count,
            SUM(CASE WHEN UnitPrice = 0 THEN 1 ELSE 0 END)
                AS zero_price_rows,
            SUM(CASE WHEN UnitPrice > 0 THEN 1 ELSE 0 END)
                AS positive_price_rows,
            SUM(CASE WHEN UnitPrice < 0 THEN 1 ELSE 0 END)
                AS negative_price_rows,
            ROUND(SUM(LineAmount), 2) AS total_line_amount
        FROM transactions
        WHERE Quantity < 0
          AND is_cancellation_invoice = 0
    """, conn)

    print(summary.to_string(index=False))

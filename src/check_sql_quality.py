
from pathlib import Path
import sqlite3
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "retail.db"

queries = {
    "Negative quantity rows": """
        SELECT
            COUNT(*) AS row_count,
            COUNT(DISTINCT InvoiceNo) AS invoice_count,
            ROUND(SUM(LineAmount), 2) AS total_line_amount
        FROM transactions
        WHERE Quantity < 0
    """,
    "Negative quantities by cancellation flag": """
        SELECT
            is_cancellation_invoice,
            COUNT(*) AS row_count,
            ROUND(SUM(LineAmount), 2) AS total_line_amount
        FROM transactions
        WHERE Quantity < 0
        GROUP BY is_cancellation_invoice
    """,
    "Product descriptions for suspicious stock codes": """
        SELECT
            StockCode,
            Description,
            COUNT(*) AS row_count,
            SUM(Quantity) AS net_quantity,
            ROUND(SUM(LineAmount), 2) AS net_line_amount
        FROM transactions
        WHERE StockCode IN ('85123A', '85099B', '22423', '23843')
        GROUP BY StockCode, Description
        ORDER BY StockCode, row_count DESC
    """,
}

with sqlite3.connect(DB_PATH) as conn:
    for title, query in queries.items():
        print(f"\n{'=' * 15} {title} {'=' * 15}")
        print(pd.read_sql_query(query, conn).to_string(index=False))

print("\nQuality checks complete.")

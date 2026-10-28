
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "retail.db"
SQL_PATH = ROOT / "sql" / "01_sales_reports.sql"

if not DB_PATH.exists():
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

sql = SQL_PATH.read_text(encoding="utf-8")

with sqlite3.connect(DB_PATH) as conn:
    conn.executescript(sql)

    reports = {
        "Monthly sales": """
            SELECT *
            FROM vw_monthly_sales
            ORDER BY sales_month
            LIMIT 12
        """,
        "Top 10 products": """
            SELECT *
            FROM vw_product_performance
            ORDER BY net_line_amount DESC
            LIMIT 10
        """,
        "Top 10 countries": """
            SELECT *
            FROM vw_country_performance
            ORDER BY net_line_amount DESC
            LIMIT 10
        """,
    }

    for title, query in reports.items():
        print(f"\n{'=' * 20} {title} {'=' * 20}")
        print(pd.read_sql_query(query, conn).to_string(index=False))

print("\nSQL reports created and executed successfully.")

from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "retail.db"
REPORT_DIR = ROOT / "reports" / "exports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

queries = {
    "monthly_sales.csv": """
        SELECT *
        FROM vw_monthly_sales
        ORDER BY sales_month
    """,
    "product_performance.csv": """
        SELECT *
        FROM vw_product_performance
        ORDER BY net_line_amount DESC
    """,
    "country_performance.csv": """
        SELECT *
        FROM vw_country_performance
        ORDER BY net_line_amount DESC
    """,
}

with sqlite3.connect(DB_PATH) as conn:
    for filename, query in queries.items():
        df = pd.read_sql_query(query, conn)
        output_path = REPORT_DIR / filename
        df.to_csv(output_path, index=False)
        print(f"{filename}: {len(df):,} rows exported")

inventory = pd.read_csv(
    ROOT / "data" / "processed" / "simulated_inventory.csv"
)

inventory.to_csv(
    REPORT_DIR / "simulated_inventory.csv",
    index=False,
)

print(
    "simulated_inventory.csv: "
    f"{len(inventory):,} rows exported"
)
print(f"\nExports saved to: {REPORT_DIR}")

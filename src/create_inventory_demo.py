
from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "database" / "retail.db"
OUTPUT_PATH = ROOT / "data" / "processed" / "simulated_inventory.csv"

OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with sqlite3.connect(DB_PATH) as conn:
    products = pd.read_sql_query("""
        SELECT
            StockCode,
            SUM(CASE
                WHEN is_cancellation_invoice = 0
                 AND Quantity > 0
                 AND UnitPrice > 0
                THEN Quantity ELSE 0
            END) AS positive_units_sold,
            COUNT(DISTINCT CASE
                WHEN is_cancellation_invoice = 0
                 AND Quantity > 0
                 AND UnitPrice > 0
                THEN InvoiceNo
            END) AS sales_invoices
        FROM transactions
        GROUP BY StockCode
    """, conn)

# Reproducible demonstration values; not real inventory records.
products["positive_units_sold"] = (
    products["positive_units_sold"].fillna(0).clip(lower=0)
)

products["avg_daily_units_sold"] = (
    products["positive_units_sold"] / 365
).round(2)

# Simulate current stock using a fixed seed so results are repeatable.
products["simulated_stock_on_hand"] = (
    products["positive_units_sold"].astype(int) % 101
)

products["simulated_reorder_point"] = (
    products["avg_daily_units_sold"] * 14
).round().astype(int)

products["simulated_stock_status"] = "Healthy"

products.loc[
    products["simulated_stock_on_hand"]
    <= products["simulated_reorder_point"],
    "simulated_stock_status"
] = "Reorder"

products.loc[
    products["simulated_stock_on_hand"] == 0,
    "simulated_stock_status"
] = "Out of stock"

products["estimated_days_of_stock"] = (
    products["simulated_stock_on_hand"]
    / products["avg_daily_units_sold"].where(
        products["avg_daily_units_sold"] > 0
    )
).round(1)

products["inventory_data_type"] = "SIMULATED — NOT ACTUAL STOCK"

products.to_csv(OUTPUT_PATH, index=False)

print(f"Products: {len(products):,}")
print(f"Saved: {OUTPUT_PATH}")
print("\nInventory status counts:")
print(products["simulated_stock_status"].value_counts().to_string())
print("\nSample:")
print(products.head(10).to_string(index=False))

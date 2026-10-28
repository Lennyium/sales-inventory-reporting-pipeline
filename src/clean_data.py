
from pathlib import Path
from datetime import datetime
import logging

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_DIR = ROOT / "logs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    filename=LOG_DIR / "cleaning.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    force=True,
)

files = list(RAW_DIR.glob("*.xlsx"))

if len(files) != 1:
    raise FileNotFoundError(
        f"Expected one Excel file in {RAW_DIR}, found {len(files)}."
    )

source_file = files[0]
frames = []

# Load both worksheets and standardize column names.

with pd.ExcelFile(source_file) as workbook:
    for sheet in workbook.sheet_names:
        df = pd.read_excel(workbook, sheet_name=sheet)

        df.columns = [
            str(col).replace("\ufeff", "").strip()
            for col in df.columns
        ]
        # Standardize source column names for the pipeline.
        df = df.rename(columns={
            "Invoice": "InvoiceNo",
            "Price": "UnitPrice",
            "Customer ID": "CustomerID",
        })

        print(f"Sheet: {sheet}")
        print("Columns:", repr(df.columns.tolist()))

        frames.append(df)
        logging.info(
            "Loaded worksheet '%s': %s rows",
            sheet,
            f"{len(df):,}",
        )

df = pd.concat(frames, ignore_index=True)

initial_rows = len(df)
logging.info("Total raw rows: %s", f"{initial_rows:,}")

# Normalize text fields without changing identifier meaning.
for col in ["InvoiceNo", "StockCode", "Description", "Country"]:
    df[col] = df[col].astype("string").str.strip()

df["Description"] = df["Description"].replace("", pd.NA)
df["Country"] = df["Country"].replace("", pd.NA)

# Convert fields to appropriate data types.
df["InvoiceDate"] = pd.to_datetime(
    df["InvoiceDate"], errors="coerce"
)
df["Quantity"] = pd.to_numeric(
    df["Quantity"], errors="coerce"
)
df["UnitPrice"] = pd.to_numeric(
    df["UnitPrice"], errors="coerce"
)
df["CustomerID"] = pd.to_numeric(
    df["CustomerID"], errors="coerce"
)

# Record quality flags BEFORE removing duplicate rows.
print("Rows before duplicate check:", len(df))
print("Exact duplicates before normalization:", df.duplicated(keep="first").sum())
print("Rows with blank descriptions:", df["Description"].isna().sum())
df["is_duplicate"] = df.duplicated(keep="first")

df["is_cancellation_invoice"] = (
    df["InvoiceNo"].str.upper().str.startswith("C", na=False)
)

df["is_negative_quantity"] = df["Quantity"] < 0
df["is_zero_quantity"] = df["Quantity"] == 0
df["is_negative_price"] = df["UnitPrice"] < 0
df["is_zero_price"] = df["UnitPrice"] == 0
df["customer_id_missing"] = df["CustomerID"].isna()
df["description_missing"] = df["Description"].isna()

df["invalid_invoice"] = df["InvoiceNo"].isna() | (
    df["InvoiceNo"] == ""
)
df["invalid_stock_code"] = df["StockCode"].isna() | (
    df["StockCode"] == ""
)
df["invalid_date"] = df["InvoiceDate"].isna()
df["invalid_quantity"] = (
    df["Quantity"].isna() | ~df["Quantity"].map(
        lambda x: pd.isna(x) or float(x).is_integer()
    )
)
df["invalid_price"] = (
    df["UnitPrice"].isna() | ~df["UnitPrice"].map(
        lambda x: pd.isna(x) or float(x) >= 0
    )
)

# Log checks before any rows are removed.
flag_columns = [
    "is_duplicate",
    "is_cancellation_invoice",
    "is_negative_quantity",
    "is_zero_quantity",
    "is_negative_price",
    "is_zero_price",
    "customer_id_missing",
    "description_missing",
    "invalid_invoice",
    "invalid_stock_code",
    "invalid_date",
    "invalid_quantity",
    "invalid_price",
]

for col in flag_columns:
    logging.info("%s: %s rows flagged", col, f"{int(df[col].sum()):,}")

# Remove exact duplicate copies, keeping the first occurrence.
duplicate_count = int(df["is_duplicate"].sum())
df = df.loc[~df["is_duplicate"]].copy()

logging.info("Exact duplicate rows removed: %s", f"{duplicate_count:,}")

# Reject rows missing essential transaction fields or containing
# invalid quantity/price values. Preserve the rejected rows separately.
invalid_mask = (
    df["invalid_invoice"]
    | df["invalid_stock_code"]
    | df["invalid_date"]
    | df["invalid_quantity"]
    | df["invalid_price"]
)

rejected = df.loc[invalid_mask].copy()
clean = df.loc[~invalid_mask].copy()

rejected_path = PROCESSED_DIR / "rejected_transactions.csv"
rejected.to_csv(rejected_path, index=False)

# Customer IDs are identifiers, not measurements.
clean["CustomerID"] = clean["CustomerID"].round().astype("Int64")

# Calculate the transaction line amount without dropping returns.
clean["LineAmount"] = clean["Quantity"] * clean["UnitPrice"]

# Save cleaned transactions and a compact quality summary.
output_path = PROCESSED_DIR / "clean_transactions.csv"
clean.to_csv(output_path, index=False)

summary = [
    ("raw_rows", initial_rows),
    ("duplicate_rows_removed", duplicate_count),
    ("rows_rejected", len(rejected)),
    ("clean_rows", len(clean)),
    ("missing_customer_ids_retained", int(clean["customer_id_missing"].sum())),
    ("missing_descriptions_retained", int(clean["description_missing"].sum())),
    ("negative_quantity_rows_retained", int(clean["is_negative_quantity"].sum())),
    ("cancellation_invoice_rows_retained", int(clean["is_cancellation_invoice"].sum())),
    ("zero_price_rows_retained", int(clean["is_zero_price"].sum())),
    ("negative_price_rows_rejected", int(rejected["is_negative_price"].sum())),
]

summary_path = PROCESSED_DIR / "cleaning_summary.csv"
pd.DataFrame(summary, columns=["check", "row_count"]).to_csv(
    summary_path, index=False
)

logging.info("Clean rows: %s", f"{len(clean):,}")
logging.info("Rejected rows: %s", f"{len(rejected):,}")
logging.info("Cleaning completed successfully.")

print(f"Raw rows: {initial_rows:,}")
print(f"Duplicate rows removed: {duplicate_count:,}")
print(f"Rejected rows: {len(rejected):,}")
print(f"Clean rows: {len(clean):,}")
print(f"Clean data: {output_path}")
print(f"Rejected data: {rejected_path}")
print(f"Summary: {summary_path}")
print(f"Log: {LOG_DIR / 'cleaning.log'}")

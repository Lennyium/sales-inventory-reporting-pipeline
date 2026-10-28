
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
REPORT_DIR = ROOT / "reports"

REPORT_DIR.mkdir(parents=True, exist_ok=True)

files = list(RAW_DIR.glob("*.xlsx"))

if len(files) != 1:
    raise FileNotFoundError(
        f"Expected one Excel file in {RAW_DIR}, found {len(files)}."
    )

file_path = files[0]
report_path = REPORT_DIR / "data_profile.txt"


aliases = {
    "invoiceno": "InvoiceNo",
    "invoice": "InvoiceNo",
    "stockcode": "StockCode",
    "description": "Description",
    "quantity": "Quantity",
    "invoicedate": "InvoiceDate",
    "unitprice": "UnitPrice",
    "price": "UnitPrice",
    "customerid": "CustomerID",
    "customer id": "CustomerID",
    "country": "Country",
}

report = [
    "ONLINE RETAIL II — DATA PROFILE",
    f"Source file: {file_path.name}",
    "Raw data is not modified by this script.",
]

with pd.ExcelFile(file_path) as workbook:
    report.append(f"\nWorksheets: {workbook.sheet_names}")

    for sheet in workbook.sheet_names:
        df = pd.read_excel(workbook, sheet_name=sheet)
        df.columns = [
            aliases.get(str(col).strip().lower(), str(col).strip())
            for col in df.columns
        ]

        report.extend([
            f"\n{'=' * 55}",
            f"WORKSHEET: {sheet}",
            f"Rows: {len(df):,}",
            f"Columns: {len(df.columns)}",
            "\nColumn names:",
            str(df.columns.tolist()),
            "\nData types:",
            df.dtypes.to_string(),
            "\nMissing values by column:",
            df.isna().sum().to_string(),
            f"\nExact duplicate rows: {df.duplicated().sum():,}",
        ])

        if "Quantity" in df:
            quantity = pd.to_numeric(
                df["Quantity"], errors="coerce"
            )
            report.extend([
                f"Negative quantities: {(quantity < 0).sum():,}",
                f"Zero quantities: {(quantity == 0).sum():,}",
                f"Invalid or missing quantities: "
                f"{quantity.isna().sum():,}",
            ])

        if "UnitPrice" in df:
            price = pd.to_numeric(
                df["UnitPrice"], errors="coerce"
            )
            report.extend([
                f"Negative prices: {(price < 0).sum():,}",
                f"Zero prices: {(price == 0).sum():,}",
                f"Invalid or missing prices: "
                f"{price.isna().sum():,}",
            ])

        if "InvoiceNo" in df:
            invoice = df["InvoiceNo"].astype("string").str.strip()
            report.append(
                f"Cancellation invoice rows: "
                f"{invoice.str.upper().str.startswith('C', na=False).sum():,}"
            )

        if "InvoiceDate" in df:
            dates = pd.to_datetime(
                df["InvoiceDate"], errors="coerce"
            )
            report.extend([
                f"Earliest valid date: {dates.min()}",
                f"Latest valid date: {dates.max()}",
                f"Invalid or missing dates: {dates.isna().sum():,}",
            ])

        for col in ["InvoiceNo", "StockCode", "CustomerID", "Country"]:
            if col in df:
                report.append(
                    f"Distinct {col} values: {df[col].nunique(dropna=True):,}"
                )

        report.extend([
            "\nFirst five rows:",
            df.head().to_string(index=False),
        ])

        del df

report_path.write_text("\n".join(report), encoding="utf-8")

print("\n".join(report[:4]))
print(f"\nFull profile saved to: {report_path}")

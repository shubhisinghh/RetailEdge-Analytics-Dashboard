"""
data_cleaning.py
----------------
Loads the raw retail sales CSV, performs cleaning and validation,
and exports a processed dataset ready for analysis.

Usage:
    python scripts/data_cleaning.py
"""

import pandas as pd
import numpy as np
import os

RAW_PATH       = "data/raw/retail_sales_raw.csv"
PROCESSED_PATH = "data/processed/retail_sales_cleaned.csv"


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["InvoiceDate"])
    print(f"[INFO] Loaded {len(df):,} rows from '{path}'")
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df.drop_duplicates()
    print(f"[INFO] Removed {before - len(df)} duplicate rows")
    return df


def fix_data_types(df: pd.DataFrame) -> pd.DataFrame:
    df["Quantity"]  = pd.to_numeric(df["Quantity"],  errors="coerce")
    df["UnitPrice"] = pd.to_numeric(df["UnitPrice"], errors="coerce")
    df["LineTotal"] = pd.to_numeric(df["LineTotal"], errors="coerce")
    df["CostPrice"] = pd.to_numeric(df["CostPrice"], errors="coerce")
    df["Discount"]  = pd.to_numeric(df["Discount"],  errors="coerce").fillna(0)
    return df


def remove_invalid_rows(df: pd.DataFrame) -> pd.DataFrame:
    before = len(df)
    df = df[df["Quantity"]  > 0]
    df = df[df["UnitPrice"] > 0]
    df = df.dropna(subset=["InvoiceNo", "InvoiceDate", "Country", "StockCode"])
    print(f"[INFO] Removed {before - len(df)} invalid / null rows")
    return df


def add_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df["Year"]        = df["InvoiceDate"].dt.year
    df["Month"]       = df["InvoiceDate"].dt.month
    df["MonthName"]   = df["InvoiceDate"].dt.strftime("%b")
    df["Quarter"]     = df["InvoiceDate"].dt.quarter.map(
                            {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"})
    df["DayOfWeek"]   = df["InvoiceDate"].dt.day_name()
    df["GrossProfit"] = (df["LineTotal"] - df["CostPrice"]).round(2)
    df["Margin_pct"]  = ((df["GrossProfit"] / df["LineTotal"]) * 100).round(2)
    return df


def flag_guest_orders(df: pd.DataFrame) -> pd.DataFrame:
    df["IsGuest"] = df["CustomerID"].apply(lambda x: x == "GUEST")
    return df


def print_summary(df: pd.DataFrame):
    print("\n── Dataset Summary ──────────────────────────────────────")
    print(f"  Total rows        : {len(df):,}")
    print(f"  Unique invoices   : {df['InvoiceNo'].nunique():,}")
    print(f"  Unique customers  : {df[df['CustomerID'] != 'GUEST']['CustomerID'].nunique():,}")
    print(f"  Countries covered : {df['Country'].nunique()}")
    print(f"  Date range        : {df['InvoiceDate'].min().date()} -> {df['InvoiceDate'].max().date()}")
    print(f"  Total revenue     : GBP {df['LineTotal'].sum():,.2f}")
    print(f"  Total gross profit: GBP {df['GrossProfit'].sum():,.2f}")
    print(f"  Avg order value   : GBP {df.groupby('InvoiceNo')['LineTotal'].sum().mean():,.2f}")
    nulls = df.isnull().sum()
    nulls = nulls[nulls > 0]
    if len(nulls):
        print(f"  Remaining nulls   :\n{nulls}")
    else:
        print("  Remaining nulls   : None")
    print("─────────────────────────────────────────────────────────\n")


def main():
    os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
    df = load_data(RAW_PATH)
    df = remove_duplicates(df)
    df = fix_data_types(df)
    df = remove_invalid_rows(df)
    df = add_derived_columns(df)
    df = flag_guest_orders(df)
    print_summary(df)
    df.to_csv(PROCESSED_PATH, index=False)
    print(f"[INFO] Cleaned data saved to '{PROCESSED_PATH}'")


if __name__ == "__main__":
    main()

"""
data_analysis.py
----------------
Performs structured business analysis on the cleaned retail sales dataset.
Produces summary tables that feed into the dashboard visualisations.

Usage:
    python scripts/data_analysis.py
"""

import pandas as pd
import numpy as np
import os

CLEANED_PATH = "data/processed/retail_sales_cleaned.csv"
OUTPUT_DIR   = "outputs"


def load_clean_data() -> pd.DataFrame:
    df = pd.read_csv(CLEANED_PATH, parse_dates=["InvoiceDate"])
    print(f"[INFO] Loaded cleaned data: {len(df):,} rows")
    return df


# ── 1. Monthly Revenue ──────────────────────────────────────────
def monthly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    monthly = (
        df.groupby(["Year", "Month", "MonthName"])
        .agg(
            Revenue=("LineTotal",    "sum"),
            Orders= ("InvoiceNo",    "nunique"),
            Units=  ("Quantity",     "sum"),
            Profit= ("GrossProfit",  "sum"),
        )
        .reset_index()
        .sort_values(["Year", "Month"])
    )
    monthly["Revenue"]  = monthly["Revenue"].round(2)
    monthly["Profit"]   = monthly["Profit"].round(2)
    monthly["AvgOrderValue"] = (monthly["Revenue"] / monthly["Orders"]).round(2)
    return monthly


# ── 2. Top Customers ────────────────────────────────────────────
def top_customers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    guests = df[df["IsGuest"] == True]
    registered = df[df["IsGuest"] == False]
    top = (
        registered.groupby(["CustomerID", "CustomerName"])
        .agg(
            TotalRevenue= ("LineTotal",   "sum"),
            TotalOrders=  ("InvoiceNo",   "nunique"),
            TotalUnits=   ("Quantity",    "sum"),
            TotalProfit=  ("GrossProfit", "sum"),
        )
        .reset_index()
        .sort_values("TotalRevenue", ascending=False)
        .head(n)
    )
    top["TotalRevenue"] = top["TotalRevenue"].round(2)
    top["TotalProfit"]  = top["TotalProfit"].round(2)
    top["AvgOrderValue"]= (top["TotalRevenue"] / top["TotalOrders"]).round(2)
    return top


# ── 3. Revenue by Country ───────────────────────────────────────
def revenue_by_country(df: pd.DataFrame) -> pd.DataFrame:
    country = (
        df.groupby("Country")
        .agg(
            Revenue= ("LineTotal",   "sum"),
            Orders=  ("InvoiceNo",   "nunique"),
            Units=   ("Quantity",    "sum"),
            Profit=  ("GrossProfit", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    country["Revenue"] = country["Revenue"].round(2)
    country["Profit"]  = country["Profit"].round(2)
    country["Margin%"] = ((country["Profit"] / country["Revenue"]) * 100).round(2)
    return country


# ── 4. Revenue by Product Category ─────────────────────────────
def revenue_by_category(df: pd.DataFrame) -> pd.DataFrame:
    cat = (
        df.groupby("Category")
        .agg(
            Revenue= ("LineTotal",   "sum"),
            Units=   ("Quantity",    "sum"),
            Profit=  ("GrossProfit", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
    )
    cat["Revenue"] = cat["Revenue"].round(2)
    cat["Profit"]  = cat["Profit"].round(2)
    cat["Margin%"] = ((cat["Profit"] / cat["Revenue"]) * 100).round(2)
    return cat


# ── 5. Top Products ─────────────────────────────────────────────
def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    prod = (
        df.groupby(["StockCode", "Description", "Category"])
        .agg(
            Revenue= ("LineTotal",   "sum"),
            Units=   ("Quantity",    "sum"),
            Profit=  ("GrossProfit", "sum"),
        )
        .reset_index()
        .sort_values("Revenue", ascending=False)
        .head(n)
    )
    prod["Revenue"] = prod["Revenue"].round(2)
    prod["Profit"]  = prod["Profit"].round(2)
    prod["Margin%"] = ((prod["Profit"] / prod["Revenue"]) * 100).round(2)
    return prod


# ── 6. Quarterly Performance ────────────────────────────────────
def quarterly_performance(df: pd.DataFrame) -> pd.DataFrame:
    q = (
        df.groupby(["Year", "Quarter"])
        .agg(
            Revenue= ("LineTotal",   "sum"),
            Orders=  ("InvoiceNo",   "nunique"),
            Profit=  ("GrossProfit", "sum"),
        )
        .reset_index()
        .sort_values(["Year", "Quarter"])
    )
    q["Revenue"] = q["Revenue"].round(2)
    q["Profit"]  = q["Profit"].round(2)
    return q


# ── 7. Day-of-Week Analysis ─────────────────────────────────────
def dow_analysis(df: pd.DataFrame) -> pd.DataFrame:
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow = (
        df.groupby("DayOfWeek")
        .agg(Revenue=("LineTotal","sum"), Orders=("InvoiceNo","nunique"))
        .reset_index()
    )
    dow["DayOfWeek"] = pd.Categorical(dow["DayOfWeek"], categories=order, ordered=True)
    dow = dow.sort_values("DayOfWeek")
    dow["Revenue"] = dow["Revenue"].round(2)
    return dow


# ── 8. RFM Segmentation ─────────────────────────────────────────
def rfm_segmentation(df: pd.DataFrame) -> pd.DataFrame:
    ref_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    rfm = (
        df[df["IsGuest"] == False]
        .groupby("CustomerID")
        .agg(
            Recency=   ("InvoiceDate", lambda x: (ref_date - x.max()).days),
            Frequency= ("InvoiceNo",   "nunique"),
            Monetary=  ("LineTotal",   "sum"),
        )
        .reset_index()
    )
    rfm["Monetary"] = rfm["Monetary"].round(2)


    rfm["R_Score"] = rfm["Recency"].rank(ascending=False, method="first").apply(
                         lambda x: min(int((x / len(rfm)) * 4) + 1, 4))
    rfm["F_Score"] = rfm["Frequency"].rank(ascending=True,  method="first").apply(
                         lambda x: min(int((x / len(rfm)) * 4) + 1, 4))
    rfm["M_Score"] = rfm["Monetary"].rank(ascending=True,   method="first").apply(
                         lambda x: min(int((x / len(rfm)) * 4) + 1, 4))
    rfm["RFM_Score"] = rfm["R_Score"] + rfm["F_Score"] + rfm["M_Score"]

    def segment(score):
        if score >= 10: return "Champions"
        elif score >= 8: return "Loyal Customers"
        elif score >= 6: return "Potential Loyalists"
        elif score >= 4: return "At Risk"
        else:            return "Lost"

    rfm["Segment"] = rfm["RFM_Score"].apply(segment)
    return rfm


def save_summary(df: pd.DataFrame, name: str):
    path = os.path.join(OUTPUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"[INFO] Saved: {path}")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = load_clean_data()

    print("\n[ANALYSIS] Running all analyses...\n")

    monthly = monthly_revenue(df)
    print("Monthly Revenue (last 3 months):")
    print(monthly.tail(3).to_string(index=False))
    save_summary(monthly, "monthly_revenue")

    top_cust = top_customers(df)
    print("\nTop 5 Customers:")
    print(top_cust.head(5)[["CustomerName","TotalRevenue","TotalOrders"]].to_string(index=False))
    save_summary(top_cust, "top_customers")

    country = revenue_by_country(df)
    print("\nRevenue by Country (Top 5):")
    print(country.head(5)[["Country","Revenue","Orders","Margin%"]].to_string(index=False))
    save_summary(country, "revenue_by_country")

    cat = revenue_by_category(df)
    print("\nRevenue by Category:")
    print(cat.to_string(index=False))
    save_summary(cat, "revenue_by_category")

    top_prod = top_products(df)
    print("\nTop 10 Products:")
    print(top_prod[["Description","Revenue","Units"]].to_string(index=False))
    save_summary(top_prod, "top_products")

    q = quarterly_performance(df)
    print("\nQuarterly Performance:")
    print(q.to_string(index=False))
    save_summary(q, "quarterly_performance")

    dow = dow_analysis(df)
    print("\nRevenue by Day of Week:")
    print(dow.to_string(index=False))
    save_summary(dow, "dow_analysis")

    rfm = rfm_segmentation(df)
    print("\nRFM Segment Distribution:")
    print(rfm["Segment"].value_counts().to_string())
    save_summary(rfm, "rfm_segmentation")

    print("\n[INFO] All analysis outputs saved to /outputs/")


if __name__ == "__main__":
    main()

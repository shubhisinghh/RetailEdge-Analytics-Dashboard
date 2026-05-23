"""
visualizations.py
-----------------
Generates all dashboard-quality charts from the cleaned retail sales data
and saves them as PNG files to the outputs/ directory.

Usage:
    python scripts/visualizations.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import os

CLEANED_PATH = "data/processed/retail_sales_cleaned.csv"
OUTPUT_DIR   = "outputs"

# ── Theme ────────────────────────────────────────────────────────
BG        = "#1E2130"
PANEL     = "#252A3D"
ACCENT1   = "#4E9AF1"
ACCENT2   = "#F1714E"
ACCENT3   = "#4EF1A0"
PURPLE    = "#C47AF1"
TEXT_MAIN = "#EAEAEA"
TEXT_DIM  = "#8A8FA8"
GRID_COL  = "#2E3450"
PALETTE   = [ACCENT1, ACCENT2, ACCENT3, PURPLE, "#F1D44E",
             "#4EE0F1", "#F14EA0", "#A0F14E", "#F1A44E", "#4EF1D4"]


def style_ax(ax, title=""):
    ax.set_facecolor(PANEL)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=TEXT_DIM, labelsize=9)
    ax.yaxis.grid(True, color=GRID_COL, linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    if title:
        ax.set_title(title, color=TEXT_MAIN, fontsize=12,
                     fontweight="bold", pad=10, loc="left")


def add_header(fig, page_title, sub):
    fig.text(0.04, 0.965, "RetailEdge Analytics Dashboard",
             color=TEXT_MAIN, fontsize=20, fontweight="bold", va="center")
    fig.text(0.04, 0.938, f"{page_title}  |  FY 2023",
             color=TEXT_DIM, fontsize=10, va="center")


def add_footer(fig):
    fig.text(0.97, 0.018, "RetailEdge Analytics  |  FY 2023  |  Python / Matplotlib",
             color=TEXT_DIM, fontsize=8, ha="right")


def load():
    df = pd.read_csv(CLEANED_PATH, parse_dates=["InvoiceDate"])
    return df


# ── Chart 1: Monthly Revenue & Profit Trend ──────────────────────
def chart_monthly_trend(df):
    monthly = (df.groupby(["Month", "MonthName"])
                 .agg(Revenue=("LineTotal", "sum"), Profit=("GrossProfit", "sum"))
                 .reset_index()
                 .sort_values("Month"))
    months = monthly["MonthName"].tolist()
    rev    = (monthly["Revenue"] / 1000).tolist()
    profit = (monthly["Profit"]  / 1000).tolist()
    x = np.arange(len(months))

    fig, ax = plt.subplots(figsize=(14, 5), facecolor=BG)
    style_ax(ax, "Monthly Revenue vs Gross Profit (GBP thousands)")
    ax.fill_between(x, rev,    alpha=0.15, color=ACCENT1)
    ax.fill_between(x, profit, alpha=0.15, color=ACCENT3)
    ax.plot(x, rev,    color=ACCENT1, lw=2.5, marker="o", markersize=6,
            markerfacecolor=BG, markeredgewidth=2, label="Revenue")
    ax.plot(x, profit, color=ACCENT3, lw=2.5, marker="s", markersize=6,
            markerfacecolor=BG, markeredgewidth=2, label="Gross Profit")
    for xi, yi in zip(x, rev):
        ax.annotate(f"£{yi:.0f}k", (xi, yi), xytext=(0, 9),
                    textcoords="offset points", ha="center",
                    color=TEXT_DIM, fontsize=7.5)
    ax.set_xticks(x); ax.set_xticklabels(months, color=TEXT_DIM)
    ax.set_ylabel("GBP (thousands)", color=TEXT_DIM, fontsize=9)
    ax.tick_params(axis="x", bottom=False)
    leg = ax.legend(facecolor=PANEL, edgecolor=GRID_COL, labelcolor=TEXT_DIM, fontsize=9)
    add_footer(fig)
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    fig.savefig(f"{OUTPUT_DIR}/chart_monthly_trend.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("[INFO] Saved chart_monthly_trend.png")


# ── Chart 2: Top 10 Customers ────────────────────────────────────
def chart_top_customers(df):
    top = (df[df["IsGuest"] == False]
             .groupby(["CustomerID","CustomerName"])
             .agg(Revenue=("LineTotal","sum"))
             .reset_index()
             .sort_values("Revenue", ascending=False)
             .head(10))
    names = top["CustomerName"].tolist()
    vals  = (top["Revenue"] / 1000).tolist()

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG)
    style_ax(ax, "Top 10 Customers by Revenue")
    colours = [ACCENT2 if i == 0 else ACCENT1 for i in range(len(names))]
    bars = ax.barh(names[::-1], vals[::-1], color=colours[::-1], height=0.62, zorder=3)
    for bar, val in zip(bars, vals[::-1]):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"£{val:.1f}k", va="center", color=TEXT_DIM, fontsize=9)
    ax.set_xlabel("Revenue (GBP thousands)", color=TEXT_DIM, fontsize=9)
    ax.tick_params(axis="y", left=False)
    ax.set_xlim(0, max(vals) * 1.18)
    add_footer(fig)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/chart_top_customers.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("[INFO] Saved chart_top_customers.png")


# ── Chart 3: Revenue by Country ──────────────────────────────────
def chart_by_country(df):
    country = (df[df["Country"] != "United Kingdom"]
                 .groupby("Country")
                 .agg(Revenue=("LineTotal","sum"))
                 .reset_index()
                 .sort_values("Revenue", ascending=False)
                 .head(10))
    names = country["Country"].tolist()
    vals  = (country["Revenue"] / 1000).tolist()

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
    style_ax(ax, "Top 10 International Markets by Revenue (excl. UK)")
    colours = [ACCENT2 if i == 0 else "#5B8CF5" for i in range(len(names))]
    bars = ax.bar(names, vals, color=colours, width=0.62, zorder=3)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"£{val:.0f}k", ha="center", color=TEXT_DIM, fontsize=8.5)
    ax.set_ylabel("Revenue (GBP thousands)", color=TEXT_DIM, fontsize=9)
    ax.tick_params(axis="x", rotation=30, bottom=False)
    ax.set_ylim(0, max(vals) * 1.18)
    add_footer(fig)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/chart_by_country.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("[INFO] Saved chart_by_country.png")


# ── Chart 4: Revenue by Category (Donut) ────────────────────────
def chart_by_category(df):
    cat = (df.groupby("Category")
             .agg(Revenue=("LineTotal","sum"))
             .reset_index()
             .sort_values("Revenue", ascending=False))
    labels = cat["Category"].tolist()
    vals   = cat["Revenue"].tolist()

    fig, ax = plt.subplots(figsize=(8, 6), facecolor=BG)
    ax.set_facecolor(BG)
    wedges, texts, autotexts = ax.pie(
        vals, labels=None, autopct="%1.1f%%",
        colors=PALETTE[:len(labels)],
        wedgeprops=dict(width=0.55, edgecolor=BG, linewidth=2),
        startangle=90, pctdistance=0.78
    )
    for at in autotexts:
        at.set_color(BG); at.set_fontsize(8); at.set_fontweight("bold")
    ax.legend(wedges, labels, loc="lower center",
              bbox_to_anchor=(0.5, -0.12), ncol=3,
              facecolor=PANEL, edgecolor=GRID_COL,
              labelcolor=TEXT_DIM, fontsize=9)
    ax.set_title("Revenue Share by Product Category",
                 color=TEXT_MAIN, fontsize=12, fontweight="bold", pad=14)
    total = sum(vals)
    ax.text(0, 0, f"£{total/1000:.0f}k\nTotal",
            ha="center", va="center", color=TEXT_MAIN,
            fontsize=12, fontweight="bold")
    add_footer(fig)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/chart_by_category.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("[INFO] Saved chart_by_category.png")


# ── Chart 5: Quarterly Grouped Bar ──────────────────────────────
def chart_quarterly(df):
    q = (df.groupby("Quarter")
           .agg(Revenue=("LineTotal","sum"), Profit=("GrossProfit","sum"))
           .reset_index()
           .sort_values("Quarter"))
    quarters = q["Quarter"].tolist()
    rev    = (q["Revenue"] / 1000).tolist()
    profit = (q["Profit"]  / 1000).tolist()
    x = np.arange(len(quarters))
    w = 0.35

    fig, ax = plt.subplots(figsize=(8, 5), facecolor=BG)
    style_ax(ax, "Quarterly Revenue vs Gross Profit")
    b1 = ax.bar(x - w/2, rev,    width=w, color=ACCENT1, label="Revenue",      zorder=3)
    b2 = ax.bar(x + w/2, profit, width=w, color=ACCENT3, label="Gross Profit", zorder=3)
    for bar, val in zip(list(b1)+list(b2), rev+profit):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.5,
                f"£{val:.0f}k", ha="center", color=TEXT_DIM, fontsize=8.5)
    ax.set_xticks(x); ax.set_xticklabels(quarters, color=TEXT_DIM)
    ax.set_ylabel("GBP (thousands)", color=TEXT_DIM, fontsize=9)
    ax.tick_params(axis="x", bottom=False)
    ax.set_ylim(0, max(rev) * 1.18)
    leg = ax.legend(facecolor=PANEL, edgecolor=GRID_COL,
                    labelcolor=TEXT_DIM, fontsize=9)
    add_footer(fig)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/chart_quarterly.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("[INFO] Saved chart_quarterly.png")


# ── Chart 6: Day-of-Week Revenue ─────────────────────────────────
def chart_dow(df):
    order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
    dow = (df.groupby("DayOfWeek")
             .agg(Revenue=("LineTotal","sum"))
             .reset_index())
    dow["DayOfWeek"] = pd.Categorical(dow["DayOfWeek"], categories=order, ordered=True)
    dow = dow.sort_values("DayOfWeek")
    vals = (dow["Revenue"] / 1000).tolist()
    days = [d[:3] for d in dow["DayOfWeek"].tolist()]

    fig, ax = plt.subplots(figsize=(9, 4), facecolor=BG)
    style_ax(ax, "Revenue by Day of Week")
    peak_idx = vals.index(max(vals))
    colours = [ACCENT2 if i == peak_idx else ACCENT1 for i in range(len(days))]
    bars = ax.bar(days, vals, color=colours, width=0.6, zorder=3)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.3,
                f"£{val:.0f}k", ha="center", color=TEXT_DIM, fontsize=8.5)
    ax.set_ylabel("Revenue (GBP thousands)", color=TEXT_DIM, fontsize=9)
    ax.tick_params(axis="x", bottom=False)
    ax.set_ylim(0, max(vals) * 1.18)
    add_footer(fig)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/chart_dow.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("[INFO] Saved chart_dow.png")


# ── Chart 7: RFM Segment Distribution ────────────────────────────
def chart_rfm(df):
    ref_date = df["InvoiceDate"].max() + pd.Timedelta(days=1)
    rfm = (df[df["IsGuest"] == False]
             .groupby("CustomerID")
             .agg(Recency=("InvoiceDate", lambda x: (ref_date - x.max()).days),
                  Frequency=("InvoiceNo","nunique"),
                  Monetary=("LineTotal","sum"))
             .reset_index())
    rfm["R"] = rfm["Recency"].rank(ascending=False,method="first").apply(lambda x:min(int((x/len(rfm))*4)+1,4))
    rfm["F"] = rfm["Frequency"].rank(ascending=True, method="first").apply(lambda x:min(int((x/len(rfm))*4)+1,4))
    rfm["M"] = rfm["Monetary"].rank(ascending=True,  method="first").apply(lambda x:min(int((x/len(rfm))*4)+1,4))
    rfm["Score"] = rfm["R"] + rfm["F"] + rfm["M"]

    def seg(s):
        if s >= 10: return "Champions"
        elif s >= 8: return "Loyal"
        elif s >= 6: return "Potential"
        elif s >= 4: return "At Risk"
        else:        return "Lost"

    rfm["Segment"] = rfm["Score"].apply(seg)
    counts = rfm["Segment"].value_counts()

    seg_order  = ["Champions","Loyal","Potential","At Risk","Lost"]
    seg_colors = [ACCENT3, ACCENT1, PURPLE, ACCENT2, "#888"]
    counts = counts.reindex(seg_order).fillna(0)

    fig, ax = plt.subplots(figsize=(9, 5), facecolor=BG)
    style_ax(ax, "RFM Customer Segmentation")
    bars = ax.bar(counts.index, counts.values,
                  color=seg_colors, width=0.6, zorder=3)
    for bar, val in zip(bars, counts.values):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+0.1,
                str(int(val)), ha="center", color=TEXT_DIM, fontsize=10,
                fontweight="bold")
    ax.set_ylabel("Number of Customers", color=TEXT_DIM, fontsize=9)
    ax.tick_params(axis="x", bottom=False)
    ax.set_ylim(0, max(counts.values) * 1.20)
    add_footer(fig)
    fig.tight_layout()
    fig.savefig(f"{OUTPUT_DIR}/chart_rfm_segments.png", dpi=150,
                bbox_inches="tight", facecolor=BG)
    plt.close()
    print("[INFO] Saved chart_rfm_segments.png")


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    df = load()
    print("[INFO] Generating all charts...\n")
    chart_monthly_trend(df)
    chart_top_customers(df)
    chart_by_country(df)
    chart_by_category(df)
    chart_quarterly(df)
    chart_dow(df)
    chart_rfm(df)
    print(f"\n[INFO] All charts saved to /{OUTPUT_DIR}/")


if __name__ == "__main__":
    main()

"""
Matplotlib visualizations for AQI analysis.

Note:
- These functions *only* visualize (no preprocessing).
- They expect DataFrames already prepared by data_analysis.py.
"""

import matplotlib.pyplot as plt
import pandas as pd


# ---------------------------------------------------------------------------
# 1. Daily AQI Comparison with Ratio
# ---------------------------------------------------------------------------
def plot_daily_comparison(df: pd.DataFrame, out: str):
    """
    Plot computed AQI vs EPA official AQI with daily ratio.
    Expects columns: date, Computed_AQI, AQI, AQI_Ratio
    """
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(df["date"], df["Computed_AQI"], label="Computed AQI", alpha=0.7)
    ax.plot(df["date"], df["AQI"], label="Official AQI (EPA)", alpha=0.7)
    ax.plot(df["date"], df["AQI_Ratio"], label="AQI Ratio (Computed / Official)", linestyle="--")
    ax.set_title("Daily AQI Comparison with Ratio")
    ax.set_xlabel("Date"); ax.set_ylabel("AQI / Ratio")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 2. Monthly Average AQI Comparison
# ---------------------------------------------------------------------------
def plot_monthly_comparison(df: pd.DataFrame, out: str):
    """
    Line plot of monthly mean Computed AQI vs EPA AQI and ratio.
    Expects columns: date, Computed_AQI, AQI, AQI_Ratio
    """
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["date"], df["Computed_AQI"], label="Computed_AQI")
    ax.plot(df["date"], df["AQI"], label="Official AQI (EPA)")
    ax.plot(df["date"], df["AQI_Ratio"], label="AQI_Ratio")
    ax.set_title("Monthly Average AQI (Computed, Official, Ratio)")
    ax.set_xlabel("Month"); ax.set_ylabel("AQI / Ratio")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 3. Yearly Average AQI Comparison
# ---------------------------------------------------------------------------
def plot_yearly_comparison(df: pd.DataFrame, out: str):
    """
    Bar chart of yearly mean Computed AQI vs EPA AQI and ratio.
    Expects columns: date, Computed_AQI, AQI, AQI_Ratio
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    years = df["date"].dt.year
    ax.bar(years - 0.2, df["Computed_AQI"], width=0.3, label="Computed_AQI")
    ax.bar(years + 0.2, df["AQI"], width=0.3, label="Official AQI (EPA)")
    ax.plot(years, df["AQI_Ratio"], "g-", label="AQI_Ratio")
    ax.set_title("Yearly Average AQI (Computed, Official, Ratio)")
    ax.set_xlabel("Year"); ax.set_ylabel("AQI / Ratio")
    ax.legend()
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 4. EPA vs Computed AQI Scatter
# ---------------------------------------------------------------------------
def plot_epa_vs_computed(df: pd.DataFrame, out: str):
    """
    Scatter plot of Computed AQI vs Official AQI (EPA).
    Expects columns: aqi_computed, aqi_epa
    """
    if not {"aqi_computed", "aqi_epa"}.issubset(df.columns):
        raise ValueError("df must have columns: aqi_computed, aqi_epa")

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(df["aqi_epa"], df["aqi_computed"], alpha=0.4)
    lims = [
        min(df["aqi_epa"].min(), df["aqi_computed"].min()),
        max(df["aqi_epa"].max(), df["aqi_computed"].max())
    ]
    ax.plot(lims, lims, "b-", alpha=0.7)  # 1:1 line
    ax.set_title("EPA vs Computed AQI")
    ax.set_xlabel("EPA AQI"); ax.set_ylabel("Computed AQI")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)


# ---------------------------------------------------------------------------
# 5. Monthly AQI Trend (overall)
# ---------------------------------------------------------------------------
def plot_monthly_trend(df: pd.DataFrame, out: str):
    """
    Simple trend of mean AQI by month.
    Expects columns: date, aqi_mean
    """
    if not {"date", "aqi_mean"}.issubset(df.columns):
        raise ValueError("df must have columns: date, aqi_mean")

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df["date"], df["aqi_mean"])
    ax.set_title("AQI Trend - Monthly (month-end)")
    ax.set_xlabel("Date"); ax.set_ylabel("Mean AQI")
    fig.tight_layout()
    fig.savefig(out)
    plt.close(fig)

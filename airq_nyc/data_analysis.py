"""
Analysis layer:
- compute AQI per row from pollutants
- compare computed vs Official AQI (EPA)
- aggregate daily/monthly/yearly trends
- produce comparison aggregates (monthly/yearly) and daily ratio for plotting

No plotting here and no file I/O here. Keep it pure analysis.
"""

from typing import Optional
import pandas as pd
from airq_nyc.aqi_calculations import final_aqi


def _clean_number(x: Optional[float]):
    """Return None for NaN floats so final_aqi can skip them gracefully."""
    try:
        import math
        return None if (isinstance(x, float) and math.isnan(x)) else x
    except Exception:
        return x


def compute_aqi_from_pollutants(df: pd.DataFrame) -> pd.DataFrame:
    """
    Row-wise AQI computation. Keeps original columns and adds:
      - aqi
      - dominant
      - category
    """
    out = df.copy()
    aqi_vals, doms, cats = [], [], []
    for _, r in out.iterrows():
        pm25 = _clean_number(r.get("pm25"))
        o3   = _clean_number(r.get("o3"))
        no2  = _clean_number(r.get("no2"))
        co   = _clean_number(r.get("co"))
        if pm25 is None and o3 is None and no2 is None and co is None:
            aqi_vals.append(pd.NA); doms.append(pd.NA); cats.append(pd.NA)
            continue
        res = final_aqi(pm25, o3, no2, co)
        aqi_vals.append(res["aqi"]); doms.append(res["dominant"]); cats.append(res["category"])
    out["aqi"], out["dominant"], out["category"] = aqi_vals, doms, cats
    return out


def compare_to_epa(df_computed: pd.DataFrame, df_epa: pd.DataFrame) -> pd.DataFrame:
    """
    Merge computed AQI and Official AQI (EPA) by date.
    Adds:
      - delta = computed - official
      - match = |delta| <= 1 (tolerance to rounding)
    """
    m = df_computed[["date", "aqi"]].merge(
        df_epa[["date", "aqi"]], on="date", how="outer", suffixes=("_computed", "_epa")
    )
    m["delta"] = m["aqi_computed"] - m["aqi_epa"]
    m["match"] = m["delta"].abs() <= 1
    return m.sort_values("date").reset_index(drop=True)


def aggregate_trend(df: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    """
    Aggregate one series of AQI values across time.
    freq: 'D' (daily), 'ME' (month-end), 'Y' (yearly)
    """
    return (df.set_index("date")
              .resample(freq)["aqi"]
              .mean()
              .reset_index(name="aqi_mean"))


# ---- Aggregations used by classic plots (no plotting here) -------------------

def aggregate_compare(df_compare: pd.DataFrame, freq: str = "ME") -> pd.DataFrame:
    """
    Aggregate the comparison DataFrame to monthly or yearly means and compute ratio.

    Returns columns:
      - date
      - Computed_AQI
      - AQI                     (Official AQI (EPA))
      - AQI_Ratio = Computed_AQI / AQI
    """
    required = {"date", "aqi_computed", "aqi_epa"}
    if not required.issubset(df_compare.columns):
        raise ValueError("df_compare must have 'date', 'aqi_computed', 'aqi_epa'")

    g = (df_compare.set_index("date")[["aqi_computed", "aqi_epa"]]
                      .resample(freq).mean())
    out = g.reset_index().rename(columns={
        "aqi_computed": "Computed_AQI",
        "aqi_epa": "AQI",
    })
    out["AQI_Ratio"] = out["Computed_AQI"] / out["AQI"].replace(0, pd.NA)
    return out


def daily_ratio(df_compare: pd.DataFrame) -> pd.DataFrame:
    """
    Daily comparison with ratio. Returns: date, Computed_AQI, AQI, AQI_Ratio
    """
    required = {"date", "aqi_computed", "aqi_epa"}
    if not required.issubset(df_compare.columns):
        raise ValueError("df_compare must have 'date', 'aqi_computed', 'aqi_epa'")

    out = df_compare[["date", "aqi_computed", "aqi_epa"]].rename(
        columns={"aqi_computed": "Computed_AQI", "aqi_epa": "AQI"}
    )
    out["AQI_Ratio"] = out["Computed_AQI"] / out["AQI"].replace(0, pd.NA)
    return out.sort_values("date").reset_index(drop=True)

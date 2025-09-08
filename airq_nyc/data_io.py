"""
Data I/O utilities:
- read pollutant CSV (raw dataset with pm25, o3, no2, co)
- read official AQI CSV (EPA dataset)

Both return tidy pandas DataFrames with a proper datetime 'date' column and
numeric pollutant columns when available.

Units expected downstream (AQI tables):
- PM2.5: µg/m³
- O3   : ppm (8-hr average). Real-world daily 8-hr ppm rarely > 0.200
- NO2  : ppb (1-hr)
- CO   : ppm (8-hr)

We auto-normalize O3 when source units look like ppb or µg/m³:
- If values look like ~10–100 → likely ppb → divide by 1000.
- If values look like ~50–200 (µg/m³) → convert µg/m³ → ppm using factor ~/1960.
We choose the conversion that yields a realistic 95th percentile ≤ ~0.404 ppm.
"""

from typing import Iterable
import logging
import pandas as pd


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    return df


def _to_numeric(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    df = df.copy()
    for c in cols:
        if c in df:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def _choose_o3_conversion(series: pd.Series) -> str:
    """
    Decide how to treat O3 series originally not in ppm.
    Returns one of: 'ppb', 'ugm3', 'none'
    """
    s = series.dropna()
    if s.empty:
        return "none"

    # Candidate conversions
    ppm_ppb = s / 1000.0          # ppb -> ppm
    ppm_ugm3 = s / 1960.0         # µg/m³ -> ppm (approx @ 25°C, 1 atm)

    # Heuristic: prefer the option that yields a realistic upper-tail (<= 0.404 ppm)
    p95_ppb = ppm_ppb.quantile(0.95)
    p95_ugm3 = ppm_ugm3.quantile(0.95)

    # If raw already seems ppm (p95 <= 0.404), keep as-is
    if s.quantile(0.95) <= 0.404:
        return "none"

    # Prefer the first candidate that looks reasonable
    if p95_ppb <= 0.404:
        return "ppb"
    if p95_ugm3 <= 0.404:
        return "ugm3"

    # Neither looks sane -> leave as-is; AQI layer will still guard with 1-hr fallback / errors
    return "none"


def _normalize_o3(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "o3" not in df:
        return df

    s = df["o3"]
    if s.dropna().empty:
        return df

    choice = _choose_o3_conversion(s)
    if choice == "ppb":
        logging.info("Detected O3 likely in ppb. Converting to ppm (/1000).")
        df["o3"] = s / 1000.0
    elif choice == "ugm3":
        logging.info("Detected O3 likely in µg/m³. Converting to ppm (÷~1960).")
        df["o3"] = s / 1960.0
    # else "none": already plausible ppm

    return df


def read_pollutants_csv(path: str) -> pd.DataFrame:
    """
    Read raw pollutant data. Expects at least a 'date' column and any subset of:
    pm25, o3, no2, co. Extra columns are preserved.

    Returns a DataFrame with:
      - date : datetime64[ns]
      - pollutant columns as float (NaN allowed)
      - O3 normalized to ppm if needed
    """
    df = pd.read_csv(path)
    df = _normalize_columns(df)

    if "date" not in df:
        for alt in ("day", "timestamp", "date_local"):
            if alt in df:
                df = df.rename(columns={alt: "date"})
                break
    if "date" not in df:
        raise ValueError("Input CSV must contain 'date' (or 'day'/'timestamp'/'date_local').")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise ValueError("Some 'date' values could not be parsed to datetime.")

    df = _to_numeric(df, ["pm25", "o3", "no2", "co"])

    # Normalize O3 to ppm, if needed
    df = _normalize_o3(df)

    return df.sort_values("date").reset_index(drop=True)


def read_epa_aqi_csv(path: str) -> pd.DataFrame:
    """
    Read official AQI data (EPA). Expects a date column and a numeric 'aqi'.

    Returns a DataFrame with:
      - date : datetime64[ns]
      - aqi  : integer/float
    """
    df = pd.read_csv(path)
    df = _normalize_columns(df)

    if "date" not in df:
        for alt in ("day", "date_local", "timestamp"):
            if alt in df:
                df = df.rename(columns={alt: "date"})
                break
    if "date" not in df:
        raise ValueError("EPA CSV must contain 'date' (or 'day'/'date_local'/'timestamp').")

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    if df["date"].isna().any():
        raise ValueError("Some 'date' values in EPA CSV could not be parsed.")

    if "aqi" not in df:
        raise ValueError("EPA CSV must contain an 'aqi' column.")

    df["aqi"] = pd.to_numeric(df["aqi"], errors="coerce")

    return df[["date", "aqi"]].sort_values("date").reset_index(drop=True)

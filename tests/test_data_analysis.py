import pandas as pd
from airq_nyc.data_analysis import compute_aqi_from_pollutants, aggregate_trend

def test_compute_columns_present():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=2),
        "pm25": [10.0, 30.0],
        "o3": [None, None],
        "no2": [None, None],
        "co": [None, None],
    })
    out = compute_aqi_from_pollutants(df)
    for c in ("aqi","dominant","category"):
        assert c in out.columns

def test_monthly_aggregate():
    df = pd.DataFrame({
        "date": pd.date_range("2024-01-01", periods=3, freq="D"),
        "pm25": [8.0, 15.0, 30.0],
        "o3": [None, None, None],
        "no2": [None, None, None],
        "co": [None, None, None],
    })
    comp = compute_aqi_from_pollutants(df)
    # use 'ME' (month-end) to avoid FutureWarning
    m = aggregate_trend(comp, "ME")
    assert len(m) == 1
    assert "aqi_mean" in m.columns

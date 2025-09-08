import pandas as pd
from airq_nyc.data_io import read_pollutants_csv
from airq_nyc.aqi_calculations import aqi_for_pollutant

def test_o3_ppb_auto_conversion(tmp_path):
    # O3 values ~ tens → should be interpreted as ppb and divided by 1000
    f = tmp_path / "o3_ppb.csv"
    f.write_text("date,pm25,o3\n2024-01-01,10,80\n2024-01-02,12,60\n")
    df = read_pollutants_csv(f)
    assert "o3" in df.columns
    # after conversion, values should be ~0.08 and ~0.06 ppm
    assert 0.05 <= df.loc[0, "o3"] <= 0.12
    assert 0.05 <= df.loc[1, "o3"] <= 0.12

def test_o3_one_hour_fallback():
    # A value above 0.200 ppm should use the O3 1-hour table, not crash
    aqi, cat = aqi_for_pollutant("o3", 0.25)  # 0.25 ppm
    # Should be unhealthy or worse (AQI >= 151 is typical here)
    assert aqi >= 101
    assert isinstance(cat, str) and len(cat) > 0

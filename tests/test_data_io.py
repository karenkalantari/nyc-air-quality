import pandas as pd
from airq_nyc.data_io import read_pollutants_csv

def test_reader_parses_date_and_numeric(tmp_path):
    f = tmp_path / "p.csv"
    f.write_text("date,pm25,o3,no2,co\n2024-01-01,12.3,80,,\n")
    df = read_pollutants_csv(f)
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    assert df["pm25"].dtype.kind in "fc"  # numeric

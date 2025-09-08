"""
run_me.py — Convenience runner for the NYC AQI project.
This script is safe to run in Spyder or by double-clicking.

It calls the CLI with sensible defaults:
- reads data/new-york-air-quality.csv
- reads data/daily_aqi_nyc.csv
- writes computed/compare/trend CSVs into results/
- generates the 5 Matplotlib plots in results/
"""

from airq_nyc.cli_app import main
import sys
from pathlib import Path


if __name__ == "__main__":
    root = Path(__file__).parent
    data_dir = root / "data"
    results = root / "results"
    results.mkdir(exist_ok=True, parents=True)

    data_raw = data_dir / "new-york-air-quality.csv"
    data_epa = data_dir / "daily_aqi_nyc.csv"

    sys.argv = [
        "airq",
        "--raw", str(data_raw),
        "--epa", str(data_epa),
        "--out", str(results / "aqi_computed.csv"),
        "--compare-out", str(results / "aqi_compare.csv"),
        "--trend", "ME",
        "--plots",
    ]

    main()

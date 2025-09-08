"""
Command-line app for the NYC AQI project.

Pipeline:
1) Read raw pollutant CSV (date, pm25, o3, no2, co)
2) Compute daily AQI per row
3) Optionally read Official AQI (EPA) CSV and compare
4) Optionally aggregate trend (daily/monthly/yearly)
5) Optionally generate Matplotlib plots (PNG)

Normal usage from terminal:
  python -m airq_nyc.cli_app \
      --raw data/new-york-air-quality.csv \
      --epa data/daily_aqi_nyc.csv \
      --out results/aqi_computed.csv \
      --compare-out results/aqi_compare.csv \
      --trend ME \
      --plots

Safety feature:
- If run with **no arguments** (e.g., pressing Run in Spyder), we try to auto-fill
  defaults using files under the repo's data/ folder, so it "just works".
"""

from pathlib import Path
import argparse
import logging
import sys

from airq_nyc.data_io import read_pollutants_csv, read_epa_aqi_csv
from airq_nyc.data_analysis import (
    compute_aqi_from_pollutants,
    compare_to_epa,
    aggregate_trend,
    aggregate_compare,
    daily_ratio,
)
from airq_nyc.visualization_mpl import (
    plot_daily_comparison,
    plot_monthly_comparison,
    plot_yearly_comparison,
    plot_epa_vs_computed,
    plot_monthly_trend,
)


def _maybe_autofill_argv_if_empty() -> None:
    """
    If the script is run with no CLI args (len(sys.argv) == 1),
    try to auto-populate sensible defaults so it works in Spyder.

    We look for:
      data/new-york-air-quality.csv
      data/daily_aqi_nyc.csv
    relative to the *project root* (two levels up from this file).
    """
    if len(sys.argv) > 1:
        return  # user supplied args; do nothing

    # Find repo root: airq_nyc/ is here, repo root is parent of parent of this file
    here = Path(__file__).resolve()
    repo_root = here.parent.parent  # .../nyc-air-quality
    data_dir = repo_root / "data"
    results_dir = repo_root / "results"

    raw_default = data_dir / "new-york-air-quality.csv"
    epa_default = data_dir / "daily_aqi_nyc.csv"

    argv = ["airq"]
    if raw_default.exists():
        argv += ["--raw", str(raw_default)]
    else:
        # No raw file found -> keep argparse behavior (will error)
        return

    if epa_default.exists():
        argv += ["--epa", str(epa_default),
                 "--compare-out", str(results_dir / "aqi_compare.csv")]

    argv += [
        "--out", str(results_dir / "aqi_computed.csv"),
        "--trend", "ME",
        "--plots",
    ]

    # Ensure results dir exists
    results_dir.mkdir(exist_ok=True, parents=True)

    print(
        "INFO: No CLI arguments detected. Using default demo arguments:\n  "
        + " ".join(argv[1:])  # skip the program name
    )
    sys.argv = argv


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    _maybe_autofill_argv_if_empty()

    p = argparse.ArgumentParser(description="Compute and analyze NYC AQI.")
    p.add_argument("--raw", required=True, help="CSV with columns: date, pm25, o3, no2, co")
    p.add_argument("--epa", help="Official AQI (EPA) CSV with columns: date, aqi")
    p.add_argument("--out", default="results/aqi_computed.csv", help="Output CSV for computed AQI")
    p.add_argument("--compare-out", default="results/aqi_compare.csv",
                   help="Output CSV for computed vs official comparison (requires --epa)")
    p.add_argument("--trend", choices=["D", "ME", "YE"],
                   help="Also write aggregated trend CSV at the given frequency")
    p.add_argument("--plots", action="store_true",
                   help="Generate Matplotlib PNG plots in results/")
    args = p.parse_args()

    # Resolve relative paths against current working directory (usually repo root)
    Path("results").mkdir(exist_ok=True, parents=True)

    # 1) Read raw pollutants
    logging.info("reading pollutants: %s", args.raw)
    df_raw = read_pollutants_csv(args.raw)

    # 2) Compute per-day AQI
    logging.info("computing AQI per day")
    df_comp = compute_aqi_from_pollutants(df_raw)
    df_comp.to_csv(args.out, index=False)
    logging.info("wrote %s", args.out)

    # 3) Optional: Official EPA comparison
    cmpdf = None
    if args.epa:
        logging.info("reading Official AQI (EPA): %s", args.epa)
        df_epa = read_epa_aqi_csv(args.epa)
        cmpdf = compare_to_epa(df_comp, df_epa)
        cmpdf.to_csv(args.compare_out, index=False)
        logging.info("wrote %s", args.compare_out)
    else:
        if args.plots:
            logging.warning("No --epa provided; comparison plots will be skipped.")

    # 4) Optional: trend aggregation
    tr = None
    if args.trend:
        # Pandas recommends 'ME' for month-end; accept 'M' for backward compat if user passes it.
        freq = "ME" if args.trend == "M" else args.trend
        tr = aggregate_trend(df_comp, freq=freq)
        out_tr = f"results/aqi_trend_{args.trend}.csv"
        tr.to_csv(out_tr, index=False)
        logging.info("wrote %s", out_tr)

    # 5) Optional: Matplotlib plots (PNG)
    if args.plots:
        logging.info("generating plots into results/")

        # 5a) If we have EPA comparison, produce classic comparison figures + scatter
        if cmpdf is not None:
            # daily ratio plot
            try:
                daily = daily_ratio(cmpdf)
                plot_daily_comparison(daily, "results/aqi_daily_comparison.png")
            except Exception as e:
                logging.warning("daily comparison plot skipped: %s", e)

            # monthly comparison plot
            try:
                month = aggregate_compare(cmpdf, freq="ME")
                plot_monthly_comparison(month, "results/aqi_monthly_lines.png")
            except Exception as e:
                logging.warning("monthly comparison plot skipped: %s", e)

            # yearly comparison plot
            try:
                year = aggregate_compare(cmpdf, freq="YE")
                plot_yearly_comparison(year, "results/aqi_yearly_bars.png")
            except Exception as e:
                logging.warning("yearly comparison plot skipped: %s", e)

            # EPA vs Computed scatter
            try:
                plot_epa_vs_computed(cmpdf, "results/aqi_epa_scatter.png")
            except Exception as e:
                logging.warning("EPA vs Computed scatter skipped: %s", e)

        # 5b) Monthly AQI trend (from computed AQI only)
        if tr is not None and (args.trend in ("M", "ME")):
            try:
                plot_monthly_trend(tr, "results/aqi_trend.png")
            except Exception as e:
                logging.warning("monthly trend plot skipped: %s", e)


if __name__ == "__main__":
    main()

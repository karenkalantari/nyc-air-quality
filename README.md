# NYC Air Quality (AQI) Project

### 🌍 Environment
- Tested on: Windows 10  
- Python: see `pyproject.toml` (`requires-python`)  

---

This project computes the Air Quality Index (AQI) for New York City from raw pollutant data (PM2.5, O₃, NO₂, CO), compares it against EPA-reported AQI values, and generates trend analyses.

The goal is to provide a clean, reproducible pipeline that others can easily install, run, and extend.

---

## ✨ Features

- 📂 Read raw pollutant CSVs, normalize headers, handle unit conversions  
- 🧮 Compute AQI using official EPA breakpoints  
- 🧪 Correct O₃ handling: auto-detect ppb→ppm, 1-hour fallback for high values  
- ✅ Compare computed AQI vs EPA daily AQI (tolerance ±1)  
- 📈 Aggregate AQI trends (daily, monthly, yearly)  
- 🖼 Generate plots:  
  - Daily comparison (bars)  
  - Monthly comparison (lines)  
  - Yearly comparison (bars)  
  - Scatter plot (EPA vs computed AQI)  
  - Monthly AQI trend (line plot)  

---

## 🔧 Installation

Open your terminal (**Anaconda Prompt on Windows**, or any terminal on Mac/Linux) and run:

```bash
git clone https://github.com/karenkalantari/nyc-air-quality.git
cd nyc-air-quality
python -m venv .venv
. .venv/Scripts/activate       # On Windows
pip install -U pip
pip install -e .[dev]
```

Dependencies are declared in `pyproject.toml`.

---

## 🚀 Usage

```bash
# The easy way (recommended)
python run_me.py

# CLI command
airq --raw data/new-york-air-quality.csv --epa data/daily_aqi_nyc.csv --plots --trend ME

# Parameters
# --raw PATH (required) : pollutant CSV with columns date, pm25, o3, no2, co
# --epa PATH (optional) : CSV with official daily AQI (date, aqi)
# --out PATH (default: results/aqi_computed.csv)
# --compare-out PATH (optional)
# --trend {D,M,ME} (optional) : Daily / Monthly / Month-End aggregation
# --plots : save plots in results/
# --seed INT (optional, default 42)

# Examples
# Compute AQI only and save results
airq --raw data/new-york-air-quality.csv --out results/aqi.csv

# Compare with EPA and save comparison table
airq --raw data/new-york-air-quality.csv --epa data/daily_aqi_nyc.csv --compare-out results/aqi_compare.csv

# Generate plots and month-end trend
airq --raw data/new-york-air-quality.csv --plots --trend ME
```

---

## 🧪 Testing

```bash
pytest -q
coverage run -m pytest && coverage report -m
```

- Tests are in `tests/` and use assertions (no print statements).  
- Floating-point values are checked with tolerances.  

---

## 🛠 Implementation Notes

- AQI is computed by the **EPA breakpoint method** (`airq_nyc/aqi_calculations.py`).  
- O₃ values that look like **ppb** are automatically converted to **ppm**.  
- O₃ > 0.200 ppm triggers the **1-hour O₃ table**.  
- Results are saved to `results/` (directory created if missing).  
- Plotting functions only visualize already-prepared data.  

---

## ⚠️ Limitations

- The two CSVs in `data/` are **small sample datasets**.  
- Large inputs may make plotting slower but calculations remain correct.  

---

## 📄 License

MIT (declared in `pyproject.toml`).

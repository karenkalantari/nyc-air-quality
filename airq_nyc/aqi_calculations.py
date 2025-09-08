"""
Air Quality Index (AQI) computations using EPA breakpoint method.

Formula inside a breakpoint:
    I = (I_hi - I_lo) / (C_hi - C_lo) * (C - C_lo) + I_lo

Expected units:
- PM2.5 : µg/m³ (24-hr)
- O3    : ppm   (8-hr avg). If O3 > 0.200 ppm, EPA uses 1-hr O3 table.
- NO2   : ppb   (1-hr)
- CO    : ppm   (8-hr)
"""

from dataclasses import dataclass
from typing import Dict, Iterable, Tuple, Optional


@dataclass
class Breakpoint:
    c_low: float
    c_high: float
    i_low: int
    i_high: int
    category: str


# ---- EPA breakpoints ---------------------------------------------------------

PM25_BP: Iterable[Breakpoint] = (
    Breakpoint(0.0, 12.0, 0, 50, "Good"),
    Breakpoint(12.1, 35.4, 51, 100, "Moderate"),
    Breakpoint(35.5, 55.4, 101, 150, "Unhealthy for Sensitive Groups"),
    Breakpoint(55.5, 150.4, 151, 200, "Unhealthy"),
    Breakpoint(150.5, 250.4, 201, 300, "Very Unhealthy"),
    Breakpoint(250.5, 500.4, 301, 500, "Hazardous"),
)

# O3 8-hour (ppm) — used up to 0.200 ppm
O3_8HR_BP: Iterable[Breakpoint] = (
    Breakpoint(0.000, 0.054, 0, 50, "Good"),
    Breakpoint(0.055, 0.070, 51, 100, "Moderate"),
    Breakpoint(0.071, 0.085, 101, 150, "Unhealthy for Sensitive Groups"),
    Breakpoint(0.086, 0.105, 151, 200, "Unhealthy"),
    Breakpoint(0.106, 0.200, 201, 300, "Very Unhealthy"),
)

# O3 1-hour (ppm) — EPA guidance: use 1-hr table when 8-hr > 0.200 ppm
# (Ranges approximate the regulatory table used for AQI > 100)
O3_1HR_BP: Iterable[Breakpoint] = (
    Breakpoint(0.125, 0.164, 101, 150, "Unhealthy for Sensitive Groups"),
    Breakpoint(0.165, 0.204, 151, 200, "Unhealthy"),
    Breakpoint(0.205, 0.404, 201, 500, "Very Unhealthy/Hazardous"),
)

NO2_BP: Iterable[Breakpoint] = (
    Breakpoint(0, 53, 0, 50, "Good"),
    Breakpoint(54, 100, 51, 100, "Moderate"),
    Breakpoint(101, 360, 101, 150, "Unhealthy for Sensitive Groups"),
    Breakpoint(361, 649, 151, 200, "Unhealthy"),
    Breakpoint(650, 1249, 201, 300, "Very Unhealthy"),
    Breakpoint(1250, 2049, 301, 400, "Hazardous"),
    Breakpoint(2050, 4049, 401, 500, "Hazardous"),
)

CO_BP: Iterable[Breakpoint] = (
    Breakpoint(0.0, 4.4, 0, 50, "Good"),
    Breakpoint(4.5, 9.4, 51, 100, "Moderate"),
    Breakpoint(9.5, 12.4, 101, 150, "Unhealthy for Sensitive Groups"),
    Breakpoint(12.5, 15.4, 151, 200, "Unhealthy"),
    Breakpoint(15.5, 30.4, 201, 300, "Very Unhealthy"),
    Breakpoint(30.5, 40.4, 301, 400, "Hazardous"),
    Breakpoint(40.5, 50.4, 401, 500, "Hazardous"),
)

BREAKPOINTS: Dict[str, Iterable[Breakpoint]] = {
    "pm25": PM25_BP,
    # O3 handled specially below (8-hr then 1-hr fallback)
    "no2": NO2_BP,
    "co": CO_BP,
}


def _linear_index(c: float, bp: Breakpoint) -> int:
    i = (bp.i_high - bp.i_low) / (bp.c_high - bp.c_low) * (c - bp.c_low) + bp.i_low
    return int(round(i))


def _validate_value(name: str, value: Optional[float]) -> float:
    if value is None:
        raise ValueError(f"No value provided for {name}")
    return float(value)


def _aqi_from_table(value: float, table: Iterable[Breakpoint]) -> Tuple[int, str]:
    for bp in table:
        if bp.c_low <= value <= bp.c_high:
            return _linear_index(value, bp), bp.category
    raise ValueError("out_of_range")


def aqi_for_pollutant(pollutant: str, value: float) -> Tuple[int, str]:
    """
    Compute AQI for a single pollutant. For O3, apply EPA rule:
    - Use 8-hr O3 table up to 0.200 ppm.
    - If > 0.200 ppm, use 1-hr O3 table.
    """
    key = pollutant.lower()
    v = _validate_value(key, value)

    if key == "o3":
        # First try 8-hr table
        try:
            return _aqi_from_table(v, O3_8HR_BP)
        except ValueError:
            # If out of 8-hr range and value is plausible, try 1-hr table
            if v <= 0 or v > 1.0:
                # Completely implausible daily 8-hr ppm → surface a clear error
                raise ValueError(f"Value {v} ppm is implausible for O3 daily average; check units.")
            try:
                return _aqi_from_table(v, O3_1HR_BP)
            except ValueError:
                raise ValueError(f"Value {v} out of range for O3 (even 1-hr). Check units.")
    else:
        if key not in BREAKPOINTS:
            raise ValueError(f"Unknown pollutant: {pollutant}")
        return _aqi_from_table(v, BREAKPOINTS[key])


def final_aqi(pm25: Optional[float] = None,
              o3: Optional[float] = None,
              no2: Optional[float] = None,
              co: Optional[float] = None) -> Dict[str, object]:
    """
    Compute the overall AQI given any subset of pollutants.
    Picks the highest sub-index as the final AQI.

    Returns dict with keys: 'aqi', 'dominant', 'category'.
    """
    results = []

    if pm25 is not None:
        a, cat = aqi_for_pollutant("pm25", pm25)
        results.append(("pm25", a, cat))

    if o3 is not None:
        a, cat = aqi_for_pollutant("o3", o3)
        results.append(("o3", a, cat))

    if no2 is not None:
        a, cat = aqi_for_pollutant("no2", no2)
        results.append(("no2", a, cat))

    if co is not None:
        a, cat = aqi_for_pollutant("co", co)
        results.append(("co", a, cat))

    if not results:
        raise ValueError("No pollutant values provided")

    dominant = max(results, key=lambda r: r[1])
    return {"aqi": dominant[1], "dominant": dominant[0], "category": dominant[2]}

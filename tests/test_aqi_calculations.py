from airq_nyc.aqi_calculations import aqi_for_pollutant, final_aqi

def test_pm25_mid_band():
    aqi, cat = aqi_for_pollutant("pm25", 20.0)
    assert 51 <= aqi <= 100
    assert "Moderate" in cat

def test_final_dominant_key_exists():
    out = final_aqi(pm25=10, o3=None, no2=None, co=None)
    assert "aqi" in out and "dominant" in out and "category" in out

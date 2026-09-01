from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.exists():
    for raw_line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY") or os.getenv("WEATHERAPI_KEY") or os.getenv("OPENWEATHER_API_KEY", "")
WEATHERAPI_BASE = "https://api.weatherapi.com/v1"


class WeatherClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or WEATHER_API_KEY

    def fetch_weather_for_city(self, city: str, country: str = "US") -> Dict[str, Any]:
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY is missing. Set it in environment variables.")

        url = f"{WEATHERAPI_BASE}/current.json"
        params = {
            "key": self.api_key,
            "q": f"{city},{country}",
            "aqi": "no",
        }
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()
        current = data.get("current", {})
        condition = current.get("condition", {})
        condition_text = str(condition.get("text", "Clear"))

        return {
            "temp": float(current.get("temp_c", 20.0)),
            "rain_1h": float(current.get("precip_mm", 0.0)),
            "snow_1h": 0.0,
            "clouds_all": float(current.get("cloud", 0.0)),
            "weather_main": condition_text,
        }

    def fetch_forecast_for_city(self, city: str, country: str = "US", days: int = 7) -> List[Dict[str, Any]]:
        if not self.api_key:
            raise ValueError("WEATHER_API_KEY is missing. Set it in environment variables.")

        url = f"{WEATHERAPI_BASE}/forecast.json"
        params = {
            "key": self.api_key,
            "q": f"{city},{country}",
            "days": max(days, 1),
            "aqi": "no",
            "alerts": "no",
        }
        response = requests.get(url, params=params, timeout=20)
        response.raise_for_status()
        payload = response.json()

        items: List[Dict[str, Any]] = []
        for day in payload.get("forecast", {}).get("forecastday", [])[:days]:
            day_data = day.get("day", {})
            condition = day.get("day", {}).get("condition", {})
            items.append(
                {
                    "temp": float(day_data.get("avgtemp_c", 20.0)),
                    "rain_1h": float(day_data.get("totalprecip_mm", 0.0)),
                    "snow_1h": float(day_data.get("totalsnow_cm", 0.0) / 10.0 if day_data.get("totalsnow_cm") is not None else 0.0),
                    "clouds_all": float(day_data.get("avghumidity", 0.0)),
                    "weather_main": str(condition.get("text", "Clear")),
                }
            )

        return items

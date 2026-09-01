from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import holidays


class FeatureBuilder:
    """Build all production features for traffic prediction from minimal user input."""

    @staticmethod
    def build_forecast_dates(start_date: str, days: int) -> List[datetime]:
        base_date = pd.to_datetime(start_date)
        return [base_date + pd.Timedelta(days=i) for i in range(days)]

    @staticmethod
    def compute_cyclical(value: float, period: float) -> Dict[str, float]:
        return {
            "sin": float(np.sin(2 * np.pi * value / period)),
            "cos": float(np.cos(2 * np.pi * value / period)),
        }

    @staticmethod
    def is_holiday(date_value: datetime) -> int:
        us_holidays = holidays.US(years=date_value.year)
        return 1 if date_value.date() in us_holidays else 0

    @staticmethod
    def get_day_of_week_features(date_value: datetime) -> Dict[str, float]:
        day_index = date_value.weekday()
        return {
            "day_of_week_num": float(day_index),
            "day_sin": float(np.sin(2 * np.pi * day_index / 7)),
            "day_cos": float(np.cos(2 * np.pi * day_index / 7)),
        }

    @staticmethod
    def build_row_for_datetime(date_value: datetime, hour: int, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        weather_main = weather_data.get("weather_main", "Clear")
        weather_main = str(weather_main).title().strip()

        numerical = {
            "holiday": FeatureBuilder.is_holiday(date_value),
            "temp": float(weather_data.get("temp", 20.0)),
            "rain_1h": float(weather_data.get("rain_1h", 0.0)),
            "snow_1h": float(weather_data.get("snow_1h", 0.0)),
            "clouds_all": float(weather_data.get("clouds_all", 0.0)),
            "year": float(date_value.year),
            "hour": float(hour),
            "month": float(date_value.month),
        }

        hour_cyc = FeatureBuilder.compute_cyclical(hour, 24)
        month_cyc = FeatureBuilder.compute_cyclical(date_value.month, 12)
        day_cfg = FeatureBuilder.get_day_of_week_features(date_value)

        row = {
            **numerical,
            "hour_sin": hour_cyc["sin"],
            "hour_cos": hour_cyc["cos"],
            "month_sin": month_cyc["sin"],
            "month_cos": month_cyc["cos"],
            "day_sin": day_cfg["day_sin"],
            "day_cos": day_cfg["day_cos"],
            "weather_main": weather_main,
        }
        return row

    @staticmethod
    def build_feature_frame(start_date: str, days: int, weather_rows: List[Dict[str, Any]], hour: int = 12) -> pd.DataFrame:
        dates = FeatureBuilder.build_forecast_dates(start_date, days)
        rows = []

        for idx, date_value in enumerate(dates):
            weather = weather_rows[idx] if idx < len(weather_rows) else weather_rows[-1]
            rows.append(FeatureBuilder.build_row_for_datetime(date_value, hour, weather))

        return pd.DataFrame(rows)


WEATHER_MAIN_MAP = {
    "Clear": "Clear",
    "Clouds": "Clouds",
    "Rain": "Rain",
    "Drizzle": "Drizzle",
    "Snow": "Snow",
    "Mist": "Mist",
    "Fog": "Fog",
    "Haze": "Haze",
    "Smoke": "Smoke",
    "Squall": "Squall",
    "Thunderstorm": "Thunderstorm",
}


def normalize_weather_main(weather_main: str) -> str:
    value = str(weather_main or "Clear").strip().title()
    return WEATHER_MAIN_MAP.get(value, "Clear")

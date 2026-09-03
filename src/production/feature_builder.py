from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Any

import numpy as np
import pandas as pd
import holidays


class FeatureBuilder:
    """
    Build all production features for traffic prediction.

    Feature schema exactly matches notebook 04.1_modeling_trial.ipynb:
      Columns: holiday, temp, rain_1h, snow_1h, clouds_all, weather_main,
               day_of_week, hour_sin, hour_cos, month_sin, month_cos
      - holiday    : str  → "Not Holiday" or holiday name (text → OHE)
      - day_of_week: str  → "Monday" / "Tuesday" / … (text → OHE)
      - weather_main: str → "Clear" / "Rain" / … (text → OHE)
    """

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
    def get_holiday_label(date_value: datetime) -> str:
        """Return the US holiday name, or 'Not Holiday'."""
        us_holidays = holidays.US(years=date_value.year)
        name = us_holidays.get(date_value.date())
        return name if name else "Not Holiday"

    @staticmethod
    def get_day_of_week(date_value: datetime) -> str:
        """Return full weekday name matching the cleaned CSV ('Monday', 'Tuesday', …)."""
        return date_value.strftime("%A")

    @staticmethod
    def build_row_for_datetime(
        date_value: datetime,
        hour: int,
        weather_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build one feature row identical to what the training notebook produces
        after dropping ["traffic_volume", "date_time", "hour", "month"].
        """
        weather_main = str(weather_data.get("weather_main", "Clear")).strip().title()

        hour_cyc = FeatureBuilder.compute_cyclical(hour, 24)
        month_cyc = FeatureBuilder.compute_cyclical(date_value.month, 12)

        raw_temp = float(weather_data.get("temp", 293.15))
        temp_kelvin = raw_temp + 273.15 if raw_temp < 200.0 else raw_temp

        return {
            # --- categorical (OHE in pipeline) ---
            "holiday":      FeatureBuilder.get_holiday_label(date_value),
            "weather_main": weather_main,
            "day_of_week":  FeatureBuilder.get_day_of_week(date_value),
            # --- numerical (StandardScaler in pipeline) ---
            "temp":      temp_kelvin,
            "rain_1h":   float(weather_data.get("rain_1h", 0.0)),
            "snow_1h":   float(weather_data.get("snow_1h", 0.0)),
            "clouds_all": float(weather_data.get("clouds_all", 0.0)),
            "hour_sin":  hour_cyc["sin"],
            "hour_cos":  hour_cyc["cos"],
            "month_sin": month_cyc["sin"],
            "month_cos": month_cyc["cos"],
        }

    @staticmethod
    def build_lag_row_for_datetime(
        date_value: datetime,
        hour: int,
        weather_data: Dict[str, Any],
        lag_1: float,
        lag_2: float,
        lag_24: float,
        lag_168: float,
        rolling_mean_6h: float,
        rolling_mean_24h: float,
    ) -> Dict[str, Any]:
        """Build one feature row containing both exogenous weather/calendar and autoregressive lags."""
        row = FeatureBuilder.build_row_for_datetime(date_value, hour, weather_data)
        row.update({
            "lag_1": float(lag_1),
            "lag_2": float(lag_2),
            "lag_24": float(lag_24),
            "lag_168": float(lag_168),
            "rolling_mean_6h": float(rolling_mean_6h),
            "rolling_mean_24h": float(rolling_mean_24h),
        })
        return row

    @staticmethod
    def build_feature_frame(
        start_date: str,
        days: int,
        weather_rows: List[Dict[str, Any]],
        hour: int = 12,
    ) -> pd.DataFrame:
        """Build a DataFrame for `days` rows at a fixed hour."""
        dates = FeatureBuilder.build_forecast_dates(start_date, days)
        rows = []
        for idx, date_value in enumerate(dates):
            weather = weather_rows[idx] if idx < len(weather_rows) else weather_rows[-1]
            rows.append(FeatureBuilder.build_row_for_datetime(date_value, hour, weather))
        return pd.DataFrame(rows)

    @staticmethod
    def build_feature_frame_hour_range(
        start_date: str,
        days: int,
        weather_rows: List[Dict[str, Any]],
        start_hour: int = 0,
        end_hour: int = 23,
    ) -> List[Dict[str, Any]]:
        """
        Build rows for every (day, hour) combination in the hour range [start_hour, end_hour].
        Returns a list of dicts each with a 'df' key (single-row DataFrame) plus 'date' and 'hour'.
        """
        dates = FeatureBuilder.build_forecast_dates(start_date, days)
        records = []
        for idx, date_value in enumerate(dates):
            weather = weather_rows[idx] if idx < len(weather_rows) else weather_rows[-1]
            for h in range(start_hour, end_hour + 1):
                row = FeatureBuilder.build_row_for_datetime(date_value, h, weather)
                records.append({
                    "date": date_value,
                    "hour": h,
                    "df": pd.DataFrame([row]),
                })
        return records


# ---------------------------------------------------------------------------
# Weather normalisation (unchanged)
# ---------------------------------------------------------------------------
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

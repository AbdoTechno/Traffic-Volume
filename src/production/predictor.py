from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import joblib
import pandas as pd

from src.production.feature_builder import FeatureBuilder, normalize_weather_main


TABULAR_MODEL_PATH = Path(__file__).resolve().parents[2] / "src" / "models" / "traffic_volume_model_pipeline.joblib"
TABULAR_METADATA_PATH = Path(__file__).resolve().parents[2] / "src" / "models" / "traffic_volume_model_metadata.json"

LAG_MODEL_PATH = Path(__file__).resolve().parents[2] / "src" / "models" / "traffic_volume_lag_pipeline.joblib"
LAG_METADATA_PATH = Path(__file__).resolve().parents[2] / "src" / "models" / "traffic_volume_lag_metadata.json"

# Typical baseline commute hourly curves for lag initialization (vehicles/hr)
WEEKDAY_BASELINE = [
    550, 420, 380, 430, 900, 2500, 5200, 6100, 5800, 4600, 4300, 4600,
    4900, 4800, 5100, 5600, 6300, 6400, 5200, 3800, 3000, 2500, 1800, 1000,
]
WEEKEND_BASELINE = [
    1100, 750, 520, 400, 450, 680, 1150, 1750, 2600, 3400, 4000, 4400,
    4600, 4550, 4500, 4450, 4400, 4200, 3800, 3200, 2700, 2300, 1800, 1300,
]


class TrafficPredictor:
    """
    Hybrid Production Traffic Predictor.
    
    Seamlessly combines:
    1. Tabular XGBoost (Notebook 04.1): Ideal for multi-day forward planning without live sensor requirements.
    2. AutoRegressive Lag-XGBoost (Notebook 04.2): Ideal for near-term momentum forecasting when live traffic sensor readings are available.
    """

    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path) if model_path else TABULAR_MODEL_PATH
        self.model = joblib.load(self.model_path)
        self.metadata = json.loads(TABULAR_METADATA_PATH.read_text(encoding="utf-8")) if TABULAR_METADATA_PATH.exists() else {}

        # Load AutoRegressive Lag Model if available
        self.lag_model = None
        self.lag_metadata = {}
        if LAG_MODEL_PATH.exists():
            try:
                self.lag_model = joblib.load(LAG_MODEL_PATH)
                if LAG_METADATA_PATH.exists():
                    self.lag_metadata = json.loads(LAG_METADATA_PATH.read_text(encoding="utf-8"))
            except Exception as e:
                print(f"[Warning] Failed to load lag model: {e}")

    # ------------------------------------------------------------------
    # Single-hour helpers (backward compatible)
    # ------------------------------------------------------------------
    def build_features(
        self,
        start_date: str,
        days: int,
        weather_rows: List[Dict[str, Any]],
        hour: int = 12,
    ) -> pd.DataFrame:
        df = FeatureBuilder.build_feature_frame(
            start_date=start_date, days=days, weather_rows=weather_rows, hour=hour
        )
        if "weather_main" in df.columns:
            df["weather_main"] = df["weather_main"].map(normalize_weather_main)
        return df

    def predict(
        self,
        start_date: str,
        days: int,
        weather_rows: List[Dict[str, Any]],
        hour: int = 12,
    ) -> List[float]:
        X = self.build_features(start_date, days, weather_rows, hour)
        preds = self.model.predict(X)
        return [float(v) for v in preds]

    def predict_for_each_day(
        self,
        start_date: str,
        days: int,
        weather_rows: List[Dict[str, Any]],
        hour: int = 12,
    ) -> List[Dict[str, Any]]:
        X = self.build_features(start_date, days, weather_rows, hour)
        preds = self.model.predict(X)
        results = []
        for index, value in enumerate(preds):
            results.append({
                "date": pd.to_datetime(start_date) + pd.Timedelta(days=index),
                "hour": hour,
                "predicted_traffic_volume": float(value),
            })
        return results

    # ------------------------------------------------------------------
    # Hybrid Hour-Range Prediction
    # ------------------------------------------------------------------
    def predict_hour_range(
        self,
        start_date: str,
        days: int,
        weather_rows: List[Dict[str, Any]],
        start_hour: int = 0,
        end_hour: int = 23,
        current_volume: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Predict traffic volume for every (day × hour) in [start_hour, end_hour].
        
        If current_volume is supplied and lag_model is loaded:
        - Day 1 uses AutoRegressive Lag-XGBoost with live momentum propagation.
        - Subsequent days seamlessly use Tabular XGBoost to avoid compounding multi-step lag drift.
        """
        dates = FeatureBuilder.build_forecast_dates(start_date, days)
        results: List[Dict[str, Any]] = []

        # Track rolling volume for lag rollouts if live reading is provided
        last_vol = float(current_volume) if current_volume is not None else None
        prev_vol = last_vol * 0.98 if last_vol is not None else None

        for day_idx, date_val in enumerate(dates):
            date_str = date_val.strftime("%Y-%m-%d")
            weather = weather_rows[day_idx] if day_idx < len(weather_rows) else weather_rows[-1]
            is_weekend = date_val.weekday() >= 5
            baseline_curve = WEEKEND_BASELINE if is_weekend else WEEKDAY_BASELINE

            # Determine whether to use Lag Model (Day 0 with live sensor reading) or Tabular Model
            use_lag = (day_idx == 0 and last_vol is not None and self.lag_model is not None)

            for h in range(start_hour, end_hour + 1):
                if use_lag:
                    # Construct lag feature row
                    lag_24_val = float(baseline_curve[h])
                    lag_168_val = float(baseline_curve[h])
                    rolling_6h = (last_vol + prev_vol + lag_24_val * 4) / 6.0
                    rolling_24h = 3250.0

                    row_dict = FeatureBuilder.build_lag_row_for_datetime(
                        date_value=date_val,
                        hour=h,
                        weather_data=weather,
                        lag_1=last_vol,
                        lag_2=prev_vol,
                        lag_24=lag_24_val,
                        lag_168=lag_168_val,
                        rolling_mean_6h=rolling_6h,
                        rolling_mean_24h=rolling_24h,
                    )
                    df_row = pd.DataFrame([row_dict])
                    if "weather_main" in df_row.columns:
                        df_row["weather_main"] = df_row["weather_main"].map(normalize_weather_main)
                    
                    pred_val = float(self.lag_model.predict(df_row)[0])
                    model_label = "AutoRegressive Lag-XGBoost"

                    # Roll forward momentum for next sequential hour
                    prev_vol = last_vol
                    last_vol = pred_val
                else:
                    # Tabular calendar + weather prediction
                    row_dict = FeatureBuilder.build_row_for_datetime(
                        date_value=date_val,
                        hour=h,
                        weather_data=weather,
                    )
                    df_row = pd.DataFrame([row_dict])
                    if "weather_main" in df_row.columns:
                        df_row["weather_main"] = df_row["weather_main"].map(normalize_weather_main)
                    
                    pred_val = float(self.model.predict(df_row)[0])
                    model_label = "Tabular XGBoost"

                results.append({
                    "date": date_str,
                    "hour": h,
                    "predicted_traffic_volume": round(max(0.0, pred_val), 2),
                    "model_used": model_label,
                })

        return results

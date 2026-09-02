from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import joblib
import pandas as pd

from src.production.feature_builder import FeatureBuilder, normalize_weather_main


MODEL_PATH = Path(__file__).resolve().parents[2] / "src" / "models" / "traffic_volume_model_pipeline.joblib"
METADATA_PATH = Path(__file__).resolve().parents[2] / "src" / "models" / "traffic_volume_model_metadata.json"


class TrafficPredictor:
    def __init__(self, model_path: str | Path | None = None):
        self.model_path = Path(model_path) if model_path else MODEL_PATH
        self.model = joblib.load(self.model_path)
        self.metadata = json.loads(METADATA_PATH.read_text(encoding="utf-8")) if METADATA_PATH.exists() else {}

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
    # Hour-range prediction (new)
    # ------------------------------------------------------------------
    def predict_hour_range(
        self,
        start_date: str,
        days: int,
        weather_rows: List[Dict[str, Any]],
        start_hour: int = 0,
        end_hour: int = 23,
    ) -> List[Dict[str, Any]]:
        """
        Predict traffic volume for every (day × hour) in [start_hour, end_hour].
        Returns a flat list ordered by date then hour.
        """
        records = FeatureBuilder.build_feature_frame_hour_range(
            start_date=start_date,
            days=days,
            weather_rows=weather_rows,
            start_hour=start_hour,
            end_hour=end_hour,
        )

        results = []
        for rec in records:
            df = rec["df"]
            if "weather_main" in df.columns:
                df = df.copy()
                df["weather_main"] = df["weather_main"].map(normalize_weather_main)
            pred = float(self.model.predict(df)[0])
            results.append({
                "date": rec["date"].strftime("%Y-%m-%d"),
                "hour": rec["hour"],
                "predicted_traffic_volume": round(pred, 2),
            })
        return results

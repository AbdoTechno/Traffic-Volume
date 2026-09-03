from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from pathlib import Path

import pandas as pd
from fastapi import APIRouter, HTTPException

from app.schemas import ForecastRequest
from src.production.feature_builder import FeatureBuilder
from src.production.predictor import TrafficPredictor
from src.production.weather_client import WeatherClient

router = APIRouter(tags=["forecast"])

predictor = TrafficPredictor()
weather_client = WeatherClient()

HISTORICAL_DATA_PATH = Path(__file__).resolve().parents[2] / "data" / "processed" / "traffic_volume_cleaned.csv"
_historical_df: pd.DataFrame | None = None


def get_historical_df() -> pd.DataFrame | None:
    global _historical_df
    if _historical_df is None and HISTORICAL_DATA_PATH.exists():
        try:
            df = pd.read_csv(HISTORICAL_DATA_PATH)
            df["date_val"] = pd.to_datetime(df["date_time"]).dt.date
            _historical_df = df
        except Exception:
            _historical_df = None
    return _historical_df


@router.get("/api/health")
def health_check() -> Dict[str, str]:
    """API health check endpoint."""
    return {"status": "ok", "message": "Traffic Volume Forecast API v2 is running"}


@router.post("/predict")
def predict(request: ForecastRequest) -> Dict[str, Any]:
    """
    Predict traffic volume for every (day × hour) combination in the requested range.

    Returns grouped results: for each day a list of hourly predictions
    plus a daily average and peak hour.
    """
    try:
        # Check if requested start_date exists in historical benchmark dataset (e.g. 2018 validation data)
        forecast_rows: List[Dict[str, Any]] = []
        is_historical = False
        hist_df = get_historical_df()

        if hist_df is not None:
            try:
                req_start = pd.to_datetime(request.start_date).date()
                for day_offset in range(request.days):
                    target_d = req_start + pd.Timedelta(days=day_offset)
                    matches = hist_df[hist_df["date_val"] == target_d]
                    if len(matches) > 0:
                        is_historical = True
                        forecast_rows.append({
                            "temp": float(matches["temp"].mean()),
                            "rain_1h": float(matches["rain_1h"].mean()),
                            "snow_1h": float(matches["snow_1h"].mean()),
                            "clouds_all": float(matches["clouds_all"].mean()),
                            "weather_main": str(matches["weather_main"].mode()[0]),
                        })
            except Exception:
                forecast_rows = []
                is_historical = False

        if not is_historical or len(forecast_rows) < request.days:
            forecast_rows = weather_client.fetch_forecast_for_city(
                request.city, request.country, request.days
            )

        if len(forecast_rows) < request.days:
            raise HTTPException(
                status_code=400,
                detail="Not enough weather forecast rows returned for the requested period.",
            )

        # Predict for every (day, hour) in the range using Hybrid Engine
        flat_preds = predictor.predict_hour_range(
            start_date=request.start_date,
            days=request.days,
            weather_rows=forecast_rows,
            start_hour=request.start_hour,
            end_hour=request.end_hour,
            current_volume=request.current_volume,
        )

        # Group by date
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for pred in flat_preds:
            grouped.setdefault(pred["date"], []).append({
                "hour": pred["hour"],
                "predicted_traffic_volume": pred["predicted_traffic_volume"],
                "model_used": pred.get("model_used", "Tabular XGBoost"),
            })

        daily_results: List[Dict[str, Any]] = []
        for date_str, hourly in grouped.items():
            volumes = [h["predicted_traffic_volume"] for h in hourly]
            peak = max(hourly, key=lambda x: x["predicted_traffic_volume"])
            daily_results.append({
                "date": date_str,
                "hourly": hourly,
                "daily_avg": round(sum(volumes) / len(volumes), 2),
                "peak_hour": peak["hour"],
                "peak_volume": peak["predicted_traffic_volume"],
                "primary_model": hourly[0].get("model_used", "Tabular XGBoost"),
            })

        return {
            "city": request.city,
            "country": request.country,
            "start_date": request.start_date,
            "days": request.days,
            "start_hour": request.start_hour,
            "end_hour": request.end_hour,
            "current_volume": request.current_volume,
            "engine": "Hybrid (Time-Series Lag + Tabular)" if request.current_volume is not None else "Tabular XGBoost",
            "predictions": daily_results,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/predict-single")
def predict_single(
    date: str,
    hour: int = 12,
    city: str = "Minneapolis",
    country: str = "US",
) -> Dict[str, Any]:
    try:
        weather = weather_client.fetch_weather_for_city(city, country)
        row = FeatureBuilder.build_row_for_datetime(
            datetime.strptime(date, "%Y-%m-%d"), hour, weather
        )
        prediction = predictor.model.predict(pd.DataFrame([row]))[0]
        return {
            "date": date,
            "hour": hour,
            "city": city,
            "predicted_traffic_volume": round(float(prediction), 2),
            "features": row,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

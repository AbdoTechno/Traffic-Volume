from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from src.production.feature_builder import FeatureBuilder
from src.production.predictor import TrafficPredictor
from src.production.weather_client import WeatherClient

app = FastAPI(title="Traffic Volume Forecast API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8001",
        "http://localhost:8001",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
        "http://traffic-volume-production.up.railway.app",
        "https://traffic-volume-production.up.railway.app",
        "null",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
static_path = Path(__file__).parent.parent / "src"
app.mount("/static", StaticFiles(directory=static_path), name="static")

predictor = TrafficPredictor()
weather_client = WeatherClient()


class ForecastRequest(BaseModel):
    start_date: str = Field(..., example="2026-09-01")
    days: int = Field(default=3, ge=1, le=3)
    city: str = Field(default="Minneapolis")
    country: str = Field(default="US")
    hour: int = Field(default=12, ge=0, le=23)


@app.get("/")
def home() -> FileResponse:
    """Serve the frontend dashboard."""
    index_path = Path(__file__).parent.parent / "src" / "index.html"
    return FileResponse(index_path, media_type="text/html")


@app.get("/api/health")
def health_check() -> Dict[str, str]:
    """API health check endpoint."""
    return {"status": "ok", "message": "Traffic Volume Forecast API is running"}


@app.post("/predict")
def predict(request: ForecastRequest) -> Dict[str, Any]:
    try:
        forecast_rows = weather_client.fetch_forecast_for_city(request.city, request.country, request.days)
        if len(forecast_rows) < request.days:
            raise HTTPException(status_code=400, detail="Not enough weather forecast rows returned for the requested period.")

        df = FeatureBuilder.build_feature_frame(
            start_date=request.start_date,
            days=request.days,
            weather_rows=forecast_rows,
            hour=request.hour,
        )
        predictions = predictor.model.predict(df)

        results = []
        for index, prediction in enumerate(predictions):
            date_value = pd.to_datetime(request.start_date) + pd.Timedelta(days=index)
            results.append({
                "date": date_value.strftime("%Y-%m-%d"),
                "hour": request.hour,
                "predicted_traffic_volume": round(float(prediction), 2),
            })

        return {
            "city": request.city,
            "country": request.country,
            "start_date": request.start_date,
            "days": request.days,
            "hour": request.hour,
            "predictions": results,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/predict-single")
def predict_single(date: str, hour: int = 12, city: str = "Minneapolis", country: str = "US") -> Dict[str, Any]:
    try:
        weather = weather_client.fetch_weather_for_city(city, country)
        row = FeatureBuilder.build_row_for_datetime(datetime.strptime(date, "%Y-%m-%d"), hour, weather)
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

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ForecastRequest(BaseModel):
    start_date: str = Field(..., json_schema_extra={"example": "2026-09-01"})
    days: int = Field(default=3, ge=1, le=3)
    city: str = Field(default="Minneapolis")
    country: str = Field(default="US")
    # Hour range: predict every hour from start_hour to end_hour (inclusive)
    start_hour: int = Field(default=8, ge=0, le=23)
    end_hour: int = Field(default=18, ge=0, le=23)
    # Optional real-time sensor observation for Live Momentum Time-Series Forecasting
    current_volume: float | None = Field(
        default=None,
        ge=0,
        le=8000,
        description="Optional live traffic volume (veh/hr). When provided, activates AutoRegressive Time-Series forecasting.",
    )

    @model_validator(mode="after")
    def validate_hour_range(self) -> "ForecastRequest":
        if self.end_hour < self.start_hour:
            raise ValueError("end_hour must be >= start_hour")
        return self

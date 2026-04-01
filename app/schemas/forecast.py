# app/schemas/forecast.py

from pydantic import BaseModel, ConfigDict
from datetime import date

class ForecastPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    predicted_units: float
    lower_bound: float
    upper_bound: float

class ForecastResponse(BaseModel):
    product_id: int
    forecast_days: int
    predictions: list[ForecastPoint]
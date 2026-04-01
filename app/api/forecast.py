# app/api/forecast.py

from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException, Depends

from app.database import get_db
from app.schemas.forecast import ForecastResponse, ForecastPoint, RestockResponse
from app.services.forecast_service import forecast
from app.services.restock_service import get_restock_recommendation

router = APIRouter(prefix="/forecast", tags=["forecast"])

@router.get("/{product_id}", response_model=ForecastResponse)
def get_forecast(product_id: int, days: int = 7):
    """
    Return a demand forecast for the next N days.
    Requires a trained model — run make train first.
    """
    try:
        df = forecast(product_id, days=days)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    predictions = [
        ForecastPoint(
            date=row["ds"].date(),
            predicted_units=max(0, round(row["yhat"], 2)),
            lower_bound=max(0, round(row["yhat_lower"], 2)),
            upper_bound=max(0, round(row["yhat_upper"], 2)),
        )
        for _, row in df.iterrows()
    ]

    return ForecastResponse(
        product_id=product_id,
        forecast_days=days,
        predictions=predictions,
    )

@router.get("/restock/{product_id}", response_model=RestockResponse)
def get_restock(product_id: int, db: Session = Depends(get_db)):
    """
    Return a recommended restock quantity
    """

    try:
        result = get_restock_recommendation(db, product_id)
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return result
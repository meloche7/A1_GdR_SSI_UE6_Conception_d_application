from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from meteo.database import SessionLocal
from meteo.services.forecast_service import get_forecasts, compute_indicators
from meteo.services.alerts_service import detect_alerts
from meteo.services.plotting_service import generate_forecast_plot

router = APIRouter(prefix="/forecast", tags=["Forecast"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/dashboard")
def dashboard(db: Session = Depends(get_db)):

    data = get_forecasts(db)

    return {
        "indicators": compute_indicators(data),
        "alerts": detect_alerts(data),
        "graph": generate_forecast_plot(data)
    }
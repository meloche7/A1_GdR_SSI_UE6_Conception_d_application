from fastapi import FastAPI
from meteo.routers.forecast_router import router as forecast_router

meteo = FastAPI(title="Hydro Dashboard SQLite")

meteo.include_router(forecast_router)
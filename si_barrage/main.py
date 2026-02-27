# Point d'entrée de l'application FastAPI principale
from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from .db import get_db
from .modules.dashboard import router as dashboard_router
from .modules.maintenance import router as maintenance_router
from .modules.meteo import router as meteo_router
from .modules.production import router as production_router

app = FastAPI(
    title="SI Barrage",
    description="API pour la gestion d'un barrage hydroélectrique",
    version="0.1.0",
)

app.include_router(dashboard_router.router, prefix="/dashboard", tags=["Dashboard"])
app.include_router(meteo_router.router, prefix="/meteo", tags=["Météo"])
app.include_router(
    maintenance_router.router, prefix="/maintenance", tags=["Maintenance"]
)
app.include_router(production_router.router, prefix="/production", tags=["Production"])


@app.get("/", tags=["Root"])
def read_root():
    return {"message": "Bienvenue sur l'API du SI Barrage"}


@app.get("/db", tags=["Database"])
def check_db_connection(db: Session = Depends(get_db)):
    """
    Checks the database connection and lists all tables.
    """
    try:
        # Execute a simple query to check the connection
        result = db.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
        tables = [row[0] for row in result]
        return {"status": "ok", "tables": tables}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

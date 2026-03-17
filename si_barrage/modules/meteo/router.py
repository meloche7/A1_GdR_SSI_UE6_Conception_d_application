# Endpoints de l'API pour la météo
import json

import plotly
import plotly.graph_objs as go
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from ...db import get_db
from .services import get_all_data, get_latest_debit, get_recent_history

router = APIRouter()

print("BON FICHER CHARGE")

templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):

    latest = get_latest_debit(db)
    history = get_recent_history(db)
    all_data = get_all_data(db)

    print("Latest:", latest)
    print("History:", history)
    print("All data:", all_data)

    if latest:
        latest_debit = latest[0]
    else:
        latest_debit = "Aucune donnée"

    if all_data:
        timestamps = [row[0] for row in all_data]
        debits = [row[1] for row in all_data]

        fig = go.Figure()
        fig.add_trace(go.Scatter(x=timestamps, y=debits, mode="lines+markers"))
        fig.update_layout(
            title="Historique des débits", xaxis_title="Temps", yaxis_title="Débit"
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        graphJSON = None

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "latest_debit": latest_debit,
            "history": history,
            "graphJSON": graphJSON,
        },
    )

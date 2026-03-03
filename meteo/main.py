print("BON FICHER CHARGE")
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
import json
import plotly
import plotly.graph_objs as go

app = FastAPI()
templates = Jinja2Templates(directory="templates")

DATABASE = "barrage.db"


def get_latest_debit():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT debit, timestamp FROM debits ORDER BY timestamp DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return row


def get_recent_history(limit=20):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute(
        "SELECT timestamp, debit FROM debits ORDER BY timestamp DESC LIMIT ?",
        (limit,)
    )
    rows = cursor.fetchall()
    conn.close()
    return rows


def get_all_data():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT timestamp, debit FROM debits ORDER BY timestamp ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):

    latest = get_latest_debit()
    history = get_recent_history()
    all_data = get_all_data()

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
            title="Historique des débits",
            xaxis_title="Temps",
            yaxis_title="Débit"
        )

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        graphJSON = None

    return templates.TemplateResponse("index.html", {
        "request": request,
        "latest_debit": latest_debit,
        "history": history,
        "graphJSON": graphJSON
    })
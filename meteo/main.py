from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")

CSV_PATH = Path("csv/meteo_data.csv")

def read_csv():
    if not CSV_PATH.exists():
        return pd.DataFrame(columns=["timestamp", "debit"])
    return pd.read_csv(CSV_PATH)

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/latest")
def latest_debit():
    df = read_csv()
    if df.empty:
        return {"debit": None, "timestamp": None}

    last_row = df.iloc[-1]
    return {
        "timestamp": str(last_row["timestamp"]),
        "debit": float(last_row["debit"])
    }

@app.get("/api/history")
def history():
    df = read_csv()
    df = df.tail(20)  # 20 derniers points
    return df.to_dict(orient="records")
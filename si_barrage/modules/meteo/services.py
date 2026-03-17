# Logique métier pour la météo
from sqlalchemy import text
from sqlalchemy.orm import Session


def get_latest_debit(db: Session):
    result = db.execute(
        text("SELECT debit_riviere_m3s, date FROM meteo ORDER BY date DESC LIMIT 1")
    )
    return [row[0] for row in result]


def get_recent_history(db: Session, limit=20):

    result = db.execute(
        text(
            "SELECT date, debit_riviere_m3s FROM meteo ORDER BY date DESC LIMIT :limit"
        ),
        {"limit": limit},
    )
    return [row for row in result]


def get_all_data(db: Session):

    result = db.execute(
        text("SELECT date, debit_riviere_m3s FROM meteo ORDER BY date ASC")
    )
    return [row for row in result]

# Logique métier pour la météo

from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_latest_releves(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère les derniers relevés météo (débit + pluviométrie)."""
    result = db.execute(
        text(
            """
            SELECT id, date, debit_riviere_m3s, pluviometrie_mm
            FROM meteo
            ORDER BY date DESC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()

    releves: List[Dict[str, Any]] = []
    for row in result:
        releves.append(
            {
                "id": row[0],
                "date": row[1],
                "debit_riviere_m3s": row[2],
                "pluviometrie_mm": row[3],
            }
        )

    return releves


def get_latest_previsions(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """Récupère les dernières prévisions météo/hydrologiques."""
    result = db.execute(
        text(
            """
            SELECT id, date_prevision, date_creation, debit_riviere_m3s_prevu, pluviometrie_mm_prevue
            FROM meteo_previsions
            ORDER BY date_prevision ASC
            LIMIT :limit
            """
        ),
        {"limit": limit},
    ).fetchall()

    previsions: List[Dict[str, Any]] = []
    for row in result:
        previsions.append(
            {
                "id": row[0],
                "date_prevision": row[1],
                "date_creation": row[2],
                "debit_riviere_m3s_prevu": row[3],
                "pluviometrie_mm_prevue": row[4],
            }
        )

    return previsions

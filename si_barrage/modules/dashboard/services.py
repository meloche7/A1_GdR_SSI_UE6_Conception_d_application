# Logique métier pour le dashboard
from typing import Any, Dict, List

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_mean_production(db: Session) -> float:
    """
    Calcule la production moyenne en MWh.
    """
    result = db.execute(
        text("SELECT AVG(production_mwh) as mean_prod FROM production")
    ).fetchone()

    if result and result[0]:
        return round(result[0], 2)
    return 0.0


def get_last_maintenance(db: Session, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Récupère les dernières maintenances.
    """
    result = db.execute(
        text("""
            SELECT id, id_equipement, nom_equipement, statut, description, date_creation
            FROM maintenance
            ORDER BY date_creation DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).fetchall()

    maintenance_list = []
    for row in result:
        maintenance_list.append(
            {
                "id": row[0],
                "id_equipement": row[1],
                "nom_equipement": row[2],
                "statut": row[3],
                "description": row[4],
                "date_creation": row[5],
            }
        )

    return maintenance_list

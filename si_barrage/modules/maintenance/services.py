from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import desc, func, text
from sqlalchemy.orm import Session

from .models import MaintenanceTicket
from .schemas import InterventionCreate, InterventionUpdate


def equipment_exists(db: Session, id_equipement: str) -> bool:
    """
    Un équipement existe si au moins une ligne de maintenance référence cet équipement.
    """
    return (
        db.query(MaintenanceTicket.id)
        .filter(MaintenanceTicket.id_equipement == id_equipement)
        .first()
        is not None
    )


def get_interventions(
    db: Session,
    id_equipement: str,
    *,
    limit: int = 50,
    offset: int = 0,
) -> List[MaintenanceTicket]:
    """
    Retourne tout l'historique d'un équipement.
    On n'affiche pas seulement les lignes 'Terminé', sinon
    les nouveaux tickets / nouvelles pannes n'apparaissent pas.
    On exclut uniquement les lignes marquées 'Supprimé'.
    """
    return (
        db.query(MaintenanceTicket)
        .filter(MaintenanceTicket.id_equipement == id_equipement)
        .filter(MaintenanceTicket.statut != "Supprimé")
        .order_by(
            desc(MaintenanceTicket.date_intervention),
            desc(MaintenanceTicket.date_creation),
            desc(MaintenanceTicket.id),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_intervention_by_id(
    db: Session, intervention_id: int
) -> Optional[MaintenanceTicket]:
    """
    Récupère une ligne de maintenance par son identifiant.
    Cette ligne sert de support au détail d'intervention.
    """
    return (
        db.query(MaintenanceTicket)
        .filter(MaintenanceTicket.id == intervention_id)
        .first()
    )


def create_intervention(
    db: Session,
    id_equipement: str,
    payload: InterventionCreate,
) -> MaintenanceTicket:
    """
    Crée une nouvelle ligne dans `maintenance`.
    Chaque nouvelle intervention sur un équipement crée
    un nouvel enregistrement pour préserver l'historique.
    """
    row = MaintenanceTicket(
        id_equipement=id_equipement,
        nom_equipement=None,
        statut=payload.statut,
        description=payload.probleme,
        date_creation=payload.date_intervention,
        ticket_id=payload.ticket_id,
        date_intervention=payload.date_intervention,
        intervenant=payload.intervenant,
        solution=payload.solution,
        duree_minutes=payload.duree_minutes,
        cout=payload.cout,
        pieces_changees=payload.pieces_changees,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_intervention(
    db: Session,
    intervention: MaintenanceTicket,
    payload: InterventionUpdate,
) -> MaintenanceTicket:
    """
    Pour préserver l'historique, on ne modifie pas la ligne existante.
    On crée une nouvelle ligne à partir de l'ancienne + des nouvelles valeurs.
    """
    data = payload.model_dump(exclude_unset=True)

    # Mapping ancien schéma -> nouveau schéma
    if "probleme" in data:
        data["description"] = data.pop("probleme")

    if "date_intervention" in data and "date_creation" not in data:
        data["date_creation"] = data["date_intervention"]

    new_row = MaintenanceTicket(
        id_equipement=intervention.id_equipement,
        nom_equipement=intervention.nom_equipement,
        statut=data.get("statut", intervention.statut),
        description=data.get("description", intervention.description),
        date_creation=data.get("date_creation", intervention.date_creation),
        ticket_id=data.get("ticket_id", intervention.ticket_id),
        date_intervention=data.get(
            "date_intervention", intervention.date_intervention
        ),
        intervenant=data.get("intervenant", intervention.intervenant),
        solution=data.get("solution", intervention.solution),
        duree_minutes=data.get("duree_minutes", intervention.duree_minutes),
        cout=data.get("cout", intervention.cout),
        pieces_changees=data.get("pieces_changees", intervention.pieces_changees),
    )

    db.add(new_row)
    db.commit()
    db.refresh(new_row)
    return new_row


def analyse_recurrent_breakdowns(
    db: Session,
    id_equipement: str,
    *,
    top_n: int = 5,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Tuple[int, List[dict], Optional[dict]]:
    """
    Analyse des problèmes récurrents d'un équipement.
    On travaille sur toutes les lignes non supprimées pour que
    les nouvelles pannes remontent aussi dans l'analyse.
    """
    query = (
        db.query(MaintenanceTicket)
        .filter(MaintenanceTicket.id_equipement == id_equipement)
        .filter(MaintenanceTicket.statut != "Supprimé")
    )

    if start_date:
        query = query.filter(
            func.coalesce(
                MaintenanceTicket.date_intervention,
                MaintenanceTicket.date_creation,
            ) >= start_date
        )

    if end_date:
        query = query.filter(
            func.coalesce(
                MaintenanceTicket.date_intervention,
                MaintenanceTicket.date_creation,
            ) <= end_date
        )

    periode = None
    if start_date or end_date:
        periode = {"start_date": start_date, "end_date": end_date}

    total = query.count()

    rows = (
        db.query(
            MaintenanceTicket.description.label("probleme"),
            func.count(MaintenanceTicket.id).label("occurrences"),
            func.min(
                func.coalesce(
                    MaintenanceTicket.date_intervention,
                    MaintenanceTicket.date_creation,
                )
            ).label("premiere_date"),
            func.max(
                func.coalesce(
                    MaintenanceTicket.date_intervention,
                    MaintenanceTicket.date_creation,
                )
            ).label("derniere_date"),
        )
        .filter(MaintenanceTicket.id_equipement == id_equipement)
        .filter(MaintenanceTicket.statut != "Supprimé")
        .filter(
            func.coalesce(
                MaintenanceTicket.date_intervention,
                MaintenanceTicket.date_creation,
            ) >= start_date
            if start_date
            else True
        )
        .filter(
            func.coalesce(
                MaintenanceTicket.date_intervention,
                MaintenanceTicket.date_creation,
            ) <= end_date
            if end_date
            else True
        )
        .group_by(MaintenanceTicket.description)
        .order_by(desc("occurrences"), desc("derniere_date"))
        .limit(top_n)
        .all()
    )

    top = [
        {
            "probleme": r.probleme,
            "occurrences": int(r.occurrences),
            "premiere_date": r.premiere_date,
            "derniere_date": r.derniere_date,
        }
        for r in rows
        if r.probleme
    ]

    return total, top, periode


# -------------------------------------------------------------------
# Partie tableau de bord / maintenance globale
# -------------------------------------------------------------------


def get_equipment_last_events(db: Session) -> List[Dict[str, Any]]:
    """
    Retourne le dernier état connu par équipement à partir de `maintenance`.
    Une seule ligne par équipement.
    On exclut les lignes supprimées.
    """
    result = db.execute(
        text("""
            WITH ranked AS (
                SELECT
                    id,
                    id_equipement,
                    COALESCE(nom_equipement, id_equipement) AS nom_equipement,
                    statut,
                    date_creation,
                    description,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_equipement
                        ORDER BY date_creation DESC, id DESC
                    ) AS rn
                FROM maintenance
                WHERE id_equipement IS NOT NULL
                  AND LENGTH(id_equipement) > 0
                  AND statut != 'Supprimé'
            )
            SELECT
                id_equipement,
                nom_equipement,
                statut,
                date_creation,
                description
            FROM ranked
            WHERE rn = 1
            ORDER BY id_equipement ASC
        """)
    ).fetchall()

    return [
        {
            "id_equipement": row[0],
            "nom_equipement": row[1],
            "statut": row[2],
            "date_creation": row[3],
            "description": row[4],
        }
        for row in result
    ]


def get_kpis(db: Session) -> Dict[str, int]:
    """
    KPI sur l'état actuel du parc.
    On compte le dernier statut connu de chaque équipement, pas tout l'historique.
    On exclut les lignes supprimées.
    """
    result = db.execute(
        text("""
            WITH ranked AS (
                SELECT
                    id,
                    id_equipement,
                    statut,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_equipement
                        ORDER BY date_creation DESC, id DESC
                    ) AS rn
                FROM maintenance
                WHERE id_equipement IS NOT NULL
                  AND LENGTH(id_equipement) > 0
                  AND statut != 'Supprimé'
            )
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN statut = 'Terminé' THEN 1 ELSE 0 END) AS termines,
                SUM(CASE WHEN statut = 'En cours' THEN 1 ELSE 0 END) AS encours,
                SUM(CASE WHEN statut = 'En attente' THEN 1 ELSE 0 END) AS attente
            FROM ranked
            WHERE rn = 1
        """)
    ).fetchone()

    return {
        "termines": result[1] or 0,
        "encours": result[2] or 0,
        "attente": result[3] or 0,
    }
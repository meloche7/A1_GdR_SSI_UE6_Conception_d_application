from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Form, HTTPException, Path, Query
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlalchemy.orm import Session

from si_barrage.db import get_db

from . import services
from .models import MaintenanceTicket
from .schemas import AnalyseRead, InterventionCreate, InterventionRead
from .tdb.router import router as tdb_router
from .ui_router import router as ui_router

router = APIRouter()

# Sous-routeurs
router.include_router(tdb_router, prefix="/tdb", tags=["TDB Maintenance"])
router.include_router(ui_router, prefix="", tags=["UI Maintenance"])


@router.post("/tickets")
async def create_ticket(
    nom: str = Form(...),
    id_equipement: str = Form(...),
    nom_equipement: str = Form(...),
    statut: str = Form(...),
    description: str = Form(...),
    date_creation: str = Form(...),
    niv_urgence: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    Création d'un ticket de maintenance.

    Logique retenue :
    - on crée une nouvelle ligne dans la table `maintenance`
    - `description` contient uniquement le problème
    - `intervenant` contient le nom du technicien
    - `solution` stocke temporairement le niveau d'urgence
    - après insertion, on recopie l'identifiant auto-généré `id`
      dans `ticket_id` pour que les nouveaux tickets aient eux aussi
      un numéro de ticket visible dans le TDB
    """
    try:
        new_ticket = MaintenanceTicket(
            id_equipement=id_equipement.strip(),
            nom_equipement=nom_equipement.strip(),
            statut=statut.strip(),
            description=description.strip(),
            date_creation=date_creation,
            intervenant=nom.strip(),
            solution=f"Niveau d'urgence: {niv_urgence.strip()}",
        )

        # Étape 1 : insertion
        db.add(new_ticket)
        db.commit()
        db.refresh(new_ticket)

        # Étape 2 : on affecte ticket_id = id
        # Cela permet d'avoir un vrai numéro de ticket
        # même pour les nouvelles lignes créées via le formulaire.
        new_ticket.ticket_id = new_ticket.id
        db.commit()

        return RedirectResponse(url="/maintenance/tdb/", status_code=303)

    except Exception as e:
        db.rollback()
        print("Erreur création ticket:", e)
        return RedirectResponse(
            url="/maintenance/nouveau-ticket?error=1",
            status_code=303,
        )


@router.get("/nouveau-ticket", response_class=HTMLResponse)
async def nouveau_ticket_page():
    """
    Formulaire HTML de création d'un nouveau ticket.
    """
    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Nouveau ticket — Maintenance</title>
        <style>
            body {
                font-family: system-ui;
                max-width: 600px;
                margin: 40px auto;
                padding: 20px;
            }
            .form-group { margin-bottom: 20px; }
            label { display: block; margin-bottom: 5px; font-weight: 500; }
            input, select, textarea {
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 16px;
                box-sizing: border-box;
            }
            .btn {
                background: #28a745;
                color: white;
                padding: 14px 28px;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                cursor: pointer;
                width: 100%;
            }
            .btn:hover { background: #218838; }
            .back-link {
                display: inline-block;
                margin-bottom: 30px;
                color: #007bff;
                text-decoration: none;
            }
            .back-link:hover { text-decoration: underline; }
            h1 { color: #333; margin-bottom: 10px; }
        </style>
    </head>
    <body>
        <a href="/maintenance/tdb/" class="back-link">← Retour au tableau de bord</a>

        <h1>➕ Nouveau ticket de maintenance</h1>

        <form action="/maintenance/tickets" method="POST">
            <div class="form-group">
                <label for="nom">Technicien :</label>
                <input type="text" id="nom" name="nom" required>
            </div>

            <div class="form-group">
                <label for="id_equipement">ID Équipement :</label>
                <input type="text" id="id_equipement" name="id_equipement" required>
            </div>

            <div class="form-group">
                <label for="nom_equipement">Nom Équipement :</label>
                <input type="text" id="nom_equipement" name="nom_equipement" required>
            </div>

            <div class="form-group">
                <label for="statut">Statut :</label>
                <select id="statut" name="statut" required>
                    <option value="">Choisir...</option>
                    <option value="En cours">En cours</option>
                    <option value="En attente">En attente</option>
                    <option value="Terminé">Terminé</option>
                </select>
            </div>

            <div class="form-group">
                <label for="niv_urgence">Niveau d'urgence :</label>
                <select id="niv_urgence" name="niv_urgence" required>
                    <option value="">Choisir...</option>
                    <option value="faible">Faible</option>
                    <option value="moyen">Moyen</option>
                    <option value="urgent">Urgent</option>
                    <option value="critique">Critique</option>
                </select>
            </div>

            <div class="form-group">
                <label for="description">Description du problème :</label>
                <textarea id="description" name="description" rows="4" required
                          placeholder="Décrivez précisément le problème rencontré..."></textarea>
            </div>

            <div class="form-group">
                <label>Date de création :</label>
                <input type="date" id="date_creation" name="date_creation" required>
            </div>

            <button type="submit" class="btn">Créer le ticket</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.get("/tickets")
def list_tickets(db: Session = Depends(get_db)):
    """
    Liste brute des tickets encore actifs.

    On exclut les lignes marquées 'Supprimé'.
    """
    tickets = (
        db.query(MaintenanceTicket)
        .filter(MaintenanceTicket.statut != "Supprimé")
        .order_by(MaintenanceTicket.id.desc())
        .all()
    )

    return [
        {
            "id": t.id,
            "ticket_id": t.ticket_id,
            "id_equipement": t.id_equipement,
            "nom_equipement": t.nom_equipement,
            "statut": t.statut,
            "description": t.description,
            "date_creation": t.date_creation,
            "intervenant": t.intervenant,
        }
        for t in tickets
    ]


@router.get(
    "/equipements/{id_equipement}/interventions",
    response_model=List[InterventionRead],
    summary="Lister l'historique d'interventions d'un équipement",
)
def get_interventions(
    id_equipement: str = Path(..., examples=["T1"]),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """
    Retourne l'historique des interventions d'un équipement.
    """
    if not services.equipment_exists(db, id_equipement):
        raise HTTPException(
            status_code=404,
            detail=f"Équipement inconnu: {id_equipement}",
        )

    interventions = services.get_interventions(
        db,
        id_equipement,
        limit=limit,
        offset=offset,
    )
    return interventions


@router.get(
    "/interventions/{intervention_id}",
    response_model=InterventionRead,
    summary="Détail d'une intervention",
)
def get_intervention_detail(
    intervention_id: int,
    db: Session = Depends(get_db),
):
    """
    Retourne le détail d'une intervention.
    """
    intervention = services.get_intervention_by_id(db, intervention_id)
    if not intervention:
        raise HTTPException(
            status_code=404,
            detail=f"Intervention introuvable: {intervention_id}",
        )
    return intervention


@router.post(
    "/equipements/{id_equipement}/interventions",
    response_model=InterventionRead,
    status_code=201,
    summary="Créer une intervention pour un équipement",
)
def create_intervention(
    payload: InterventionCreate,
    id_equipement: str = Path(..., examples=["T1"]),
    db: Session = Depends(get_db),
):
    """
    Crée une intervention métier pour un équipement donné.
    """
    if not services.equipment_exists(db, id_equipement):
        raise HTTPException(
            status_code=404,
            detail=f"Équipement inconnu: {id_equipement}",
        )

    if payload.ticket_id is not None:
        ticket = (
            db.query(MaintenanceTicket)
            .filter(MaintenanceTicket.id == payload.ticket_id)
            .first()
        )
        if not ticket:
            raise HTTPException(
                status_code=404,
                detail=f"Ticket introuvable: {payload.ticket_id}",
            )
        if ticket.id_equipement != id_equipement:
            raise HTTPException(
                status_code=400,
                detail="ticket_id ne correspond pas à l'équipement demandé",
            )

    created = services.create_intervention(db, id_equipement, payload)
    return created


@router.get(
    "/equipements/{id_equipement}/interventions/analyse",
    response_model=AnalyseRead,
    summary="Analyse des pannes récurrentes (top N problèmes)",
)
def analyse_interventions(
    id_equipement: str = Path(..., examples=["T1"]),
    top_n: int = Query(5, ge=1, le=50),
    start_date: Optional[str] = Query(
        None,
        description="Filtre date ISO YYYY-MM-DD (inclusive)",
    ),
    end_date: Optional[str] = Query(
        None,
        description="Filtre date ISO YYYY-MM-DD (inclusive)",
    ),
    db: Session = Depends(get_db),
):
    """
    Retourne l'analyse des pannes récurrentes d'un équipement.
    """
    if not services.equipment_exists(db, id_equipement):
        raise HTTPException(
            status_code=404,
            detail=f"Équipement inconnu: {id_equipement}",
        )

    for label, value in [("start_date", start_date), ("end_date", end_date)]:
        if value is not None:
            try:
                date.fromisoformat(value)
            except Exception:
                raise HTTPException(
                    status_code=422,
                    detail=f"{label} doit être au format ISO YYYY-MM-DD",
                )

    total, top, periode = services.analyse_recurrent_breakdowns(
        db,
        id_equipement,
        top_n=top_n,
        start_date=start_date,
        end_date=end_date,
    )

    return {
        "id_equipement": id_equipement,
        "total_interventions": total,
        "top_problemes": top,
        "periode": periode,
    }


@router.delete("/tickets/{ticket_id}")
async def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """
    Suppression logique d'un ticket.

    On ne supprime pas physiquement la ligne de la base.
    On la marque comme 'Supprimé' pour :
    - garder la traçabilité
    - masquer la ligne dans le TDB
    - exclure la ligne des KPI et de l'historique affiché

    Important :
    ici `ticket_id` correspond à l'identifiant réel de la ligne
    dans la table `maintenance`.
    """
    try:
        ticket = (
            db.query(MaintenanceTicket)
            .filter(MaintenanceTicket.id == ticket_id)
            .first()
        )

        if not ticket:
            return Response(
                status_code=404,
                content="Ticket introuvable.",
            )

        if ticket.statut == "Supprimé":
            return Response(
                status_code=200,
                content="Le ticket était déjà supprimé.",
            )

        ticket.statut = "Supprimé"
        db.commit()

        return Response(
            status_code=200,
            content=f"Suppression effectuée avec succès pour l'équipement {ticket.id_equipement}.",
        )

    except Exception as e:
        db.rollback()
        print("Erreur suppression:", e)
        return Response(
            status_code=500,
            content="Erreur lors de la suppression.",
        )
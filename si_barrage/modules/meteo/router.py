# Endpoints de l'API pour la météo
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ...db import get_db
from . import services

router = APIRouter()


@router.get("/releves")
def get_releves(db: Session = Depends(get_db)):
    """Retourne les derniers relevés météo en JSON."""
    return services.get_latest_releves(db)


@router.get("/previsions")
def get_previsions(db: Session = Depends(get_db)):
    """Retourne les dernières prévisions météo en JSON."""
    return services.get_latest_previsions(db)


@router.get("/releves/html", response_class=HTMLResponse)
def get_releves_html(db: Session = Depends(get_db)):
    """Retourne le HTML des derniers relevés météo (pour le dashboard HTMX)."""
    releves = services.get_latest_releves(db, limit=10)

    rows = ""
    for r in releves:
        rows += f"""
        <tr>
            <td>{r['date']}</td>
            <td>{r['debit_riviere_m3s']}</td>
            <td>{r['pluviometrie_mm']}</td>
        </tr>
        """

    html = f"""
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Débit (m³/s)</th>
                <th>Pluviométrie (mm)</th>
            </tr>
        </thead>
        <tbody>
            {rows if rows else '<tr><td colspan="3" style="text-align: center;">Aucun relevé trouvé</td></tr>'}
        </tbody>
    </table>
    """
    return HTMLResponse(content=html)


@router.get("/previsions/html", response_class=HTMLResponse)
def get_previsions_html(db: Session = Depends(get_db)):
    """Retourne le HTML des prévisions météo (pour le dashboard HTMX)."""
    previsions = services.get_latest_previsions(db, limit=10)

    rows = ""
    for p in previsions:
        rows += f"""
        <tr>
            <td>{p['date_prevision']}</td>
            <td>{p['debit_riviere_m3s_prevu']}</td>
            <td>{p['pluviometrie_mm_prevue']}</td>
            <td>{p['date_creation']}</td>
        </tr>
        """

    html = f"""
    <table>
        <thead>
            <tr>
                <th>Date prévision</th>
                <th>Débit prévu (m³/s)</th>
                <th>Pluviométrie prévue (mm)</th>
                <th>Date création</th>
            </tr>
        </thead>
        <tbody>
            {rows if rows else '<tr><td colspan="4" style="text-align: center;">Aucune prévision trouvée</td></tr>'}
        </tbody>
    </table>
    """
    return HTMLResponse(content=html)

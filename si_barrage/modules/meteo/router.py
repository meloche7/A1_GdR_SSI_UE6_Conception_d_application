# Endpoints de l'API pour la météo
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ...db import get_db
from . import services
from .router_dashboard import router as dashboard_router

router = APIRouter()

router.include_router(dashboard_router, prefix="", tags=["Dashboard HTMX"])


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
            <td>{r["date"]}</td>
            <td>{r["debit_riviere_m3s"]}</td>
            <td>{r["pluviometrie_mm"]}</td>
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
            <td>{p["date_prevision"]}</td>
            <td>{p["debit_riviere_m3s_prevu"]}</td>
            <td>{p["pluviometrie_mm_prevue"]}</td>
            <td>{p["date_creation"]}</td>
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


@router.get("/api/debit-reel", response_class=HTMLResponse)
async def get_debit_reel_html(db: Session = Depends(get_db)):
    """Retourne le débit en temps réel (dernier relevé)."""
    releves = services.get_latest_releves(db, limit=1)
    if not releves:
        return HTMLResponse(
            content="<div style='text-align:center;color:#999;'>Aucun relevé</div>"
        )

    last = releves[0]
    html = f"""
    <div class="metric-value">{last["debit_riviere_m3s"]:.1f}</div>
    <div class="metric-unit">m³/s</div>
    """
    return HTMLResponse(content=html)


@router.get("/api/pluie-actuelle", response_class=HTMLResponse)
async def get_pluie_actuelle_html(db: Session = Depends(get_db)):
    """Retourne la pluie actuelle (dernier relevé)."""
    releves = services.get_latest_releves(db, limit=1)
    if not releves:
        return HTMLResponse(
            content="<div style='text-align:center;color:#999;'>Aucun relevé</div>"
        )

    last = releves[0]
    html = f"""
    <div class="metric-value">{last["pluviometrie_mm"]:.1f}</div>
    <div class="metric-unit">mm</div>
    """
    return HTMLResponse(content=html)


@router.get("/api/tendance", response_class=HTMLResponse)
async def get_tendance_html(db: Session = Depends(get_db)):
    """Retourne la tendance du débit."""
    releves = services.get_latest_releves(db, limit=2)
    if len(releves) < 2:
        tendance = "➡️ Stable"
    else:
        dernier = releves[0]["debit_riviere_m3s"]
        precedent = releves[1]["debit_riviere_m3s"]
        if dernier > precedent * 1.1:
            tendance = "📈 Hausse"
        elif dernier < precedent * 0.9:
            tendance = "📉 Baisse"
        else:
            tendance = "➡️ Stable"

    html = f"""
    <div class="metric-value" style="font-size: 2rem;">{tendance}</div>
    """
    return HTMLResponse(content=html)


@router.get("/api/mean-production", response_class=HTMLResponse)
async def get_mean_production_html(db: Session = Depends(get_db)):
    """
    Retourne le HTML de l'indicateur de production moyenne.
    """
    mean_prod = services.get_mean_production(db)

    html = f"""
    <div class="metric-value">{mean_prod}</div>
    <div class="metric-unit">MWh</div>
    """
    return HTMLResponse(content=html)


@router.get("/api/last-maintenance", response_class=HTMLResponse)
async def get_last_maintenance_html(db: Session = Depends(get_db)):
    """
    Retourne le HTML du tableau des dernières maintenances.
    """
    maintenances = services.get_last_maintenance(db, limit=10)

    # Construire le HTML du tableau
    rows = ""
    for m in maintenances:
        status_class = (
            f"status-{m['statut'].lower().replace('é', 'e').replace(' ', '-')}"
        )
        rows += f"""
        <tr>
            <td>{m["id_equipement"]}</td>
            <td>{m["nom_equipement"]}</td>
            <td><span class="status-badge {status_class}">{m["statut"]}</span></td>
            <td>{m["description"]}</td>
            <td>{m["date_creation"]}</td>
        </tr>
        """

    html = f"""
    <table>
        <thead>
            <tr>
                <th>ID Équipement</th>
                <th>Nom</th>
                <th>Statut</th>
                <th>Description</th>
                <th>Date</th>
            </tr>
        </thead>
        <tbody>
            {rows if rows else '<tr><td colspan="5" style="text-align: center;">Aucune maintenance trouvée</td></tr>'}
        </tbody>
    </table>
    """
    return HTMLResponse(content=html)


@router.get("/api/debit-graph", response_class=HTMLResponse)
async def get_debit_graph_html(db: Session = Depends(get_db)):
    """Retourne un graphique des débits réels et prévus avec axes."""
    releves = services.get_latest_releves(db, limit=15)
    previsions = services.get_latest_previsions(db, limit=15)

    values_reel = [r["debit_riviere_m3s"] for r in releves]
    values_prev = [p["debit_riviere_m3s_prevu"] for p in previsions]

    # Assurer que les deux listes ont la même longueur
    max_len = max(len(values_reel), len(values_prev))
    if len(values_reel) < max_len:
        values_reel += (
            [values_reel[-1]] * (max_len - len(values_reel))
            if values_reel
            else [0] * max_len
        )
    if len(values_prev) < max_len:
        values_prev += (
            [values_prev[-1]] * (max_len - len(values_prev))
            if values_prev
            else [0] * max_len
        )

    graph = services.render_graph_with_axes(
        values_reel, values_prev, y_label="Débit (m³/s)"
    )

    html = f"""
    {graph}
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color color-real"></div>
            <span>Débit réel</span>
        </div>
        <div class="legend-item">
            <div class="legend-color color-prev"></div>
            <span>Débit prévisionnel</span>
        </div>
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/api/historique-debits", response_class=HTMLResponse)
async def get_historique_debits_html(db: Session = Depends(get_db)):
    """Retourne un tableau d'historique des débits."""
    releves = services.get_latest_releves(db, limit=10)
    rows = ""
    for r in releves:
        rows += f"""
        <tr>
            <td>{r["date"]}</td>
            <td>{r["debit_riviere_m3s"]:.1f}</td>
        </tr>
        """

    html = f"""
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Débit (m³/s)</th>
            </tr>
        </thead>
        <tbody>
            {rows if rows else '<tr><td colspan="2" style="text-align: center;">Aucun relevé trouvé</td></tr>'}
        </tbody>
    </table>
    """
    return HTMLResponse(content=html)


@router.get("/api/historique-pluie", response_class=HTMLResponse)
async def get_historique_pluie_html(db: Session = Depends(get_db)):
    """Retourne un tableau d'historique des pluies."""
    releves = services.get_latest_releves(db, limit=10)
    rows = ""
    for r in releves:
        rows += f"""
        <tr>
            <td>{r["date"]}</td>
            <td>{r["pluviometrie_mm"]:.1f}</td>
        </tr>
        """

    html = f"""
    <table>
        <thead>
            <tr>
                <th>Date</th>
                <th>Pluie (mm)</th>
            </tr>
        </thead>
        <tbody>
            {rows if rows else '<tr><td colspan="2" style="text-align: center;">Aucun relevé trouvé</td></tr>'}
        </tbody>
    </table>
    """
    return HTMLResponse(content=html)


@router.get("/api/pluie-graph", response_class=HTMLResponse)
async def get_pluie_graph_html(db: Session = Depends(get_db)):
    """Retourne un graphique des pluies réelles et prévues avec axes."""
    releves = services.get_latest_releves(db, limit=15)
    previsions = services.get_latest_previsions(db, limit=15)

    values_reel = [r["pluviometrie_mm"] for r in releves]
    values_prev = [p["pluviometrie_mm_prevue"] for p in previsions]

    # Assurer que les deux listes ont la même longueur
    max_len = max(len(values_reel), len(values_prev))
    if len(values_reel) < max_len:
        values_reel += (
            [values_reel[-1]] * (max_len - len(values_reel))
            if values_reel
            else [0] * max_len
        )
    if len(values_prev) < max_len:
        values_prev += (
            [values_prev[-1]] * (max_len - len(values_prev))
            if values_prev
            else [0] * max_len
        )

    graph = services.render_graph_with_axes(
        values_reel, values_prev, y_label="Pluie (mm)"
    )

    html = f"""
    {graph}
    <div class="legend">
        <div class="legend-item">
            <div class="legend-color color-real"></div>
            <span>Pluie réelle</span>
        </div>
        <div class="legend-item">
            <div class="legend-color color-prev"></div>
            <span>Pluie prévue</span>
        </div>
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/api/estimation-crue", response_class=HTMLResponse)
async def get_estimation_crue_html(db: Session = Depends(get_db)):
    """Retourne une estimation simple du risque de crue."""
    releves = services.get_latest_releves(db, limit=1)
    previsions = services.get_latest_previsions(db, limit=3)

    if not releves:
        return HTMLResponse(
            content="<div style='text-align:center;color:#999;'>Aucune donnée</div>"
        )

    dernier_debit = releves[0]["debit_riviere_m3s"]
    prochains = [p["debit_riviere_m3s_prevu"] for p in previsions]
    max_prevision = max(prochains) if prochains else dernier_debit

    score = max(dernier_debit, max_prevision)
    niveau = "Faible"
    couleur = "#15803d"
    emoji = "✅"
    if score > 80:
        niveau = "Élevé"
        couleur = "#dc2626"
        emoji = "🚨"
    elif score > 50:
        niveau = "Modéré"
        couleur = "#d97706"
        emoji = "⚠️"

    html = f"""
    <div class="estimation-box">
        <div style="font-size: 2.5rem; color: {couleur}; margin-bottom: 10px;">{emoji} {niveau}</div>
        <div style="font-size: 0.95rem; color: #555;">Débit max prévu : <strong>{score:.1f} m³/s</strong></div>
    </div>
    """
    return HTMLResponse(content=html)


@router.get("/api/conseils-operation", response_class=HTMLResponse)
async def get_conseils_operation_html(db: Session = Depends(get_db)):
    """Retourne des conseils d'exploitation simple basés sur les données météo."""
    releves = services.get_latest_releves(db, limit=1)
    if not releves:
        return HTMLResponse(
            content="<div style='text-align:center;color:#999;'>Aucune donnée</div>"
        )

    debit = releves[0]["debit_riviere_m3s"]
    if debit > 80:
        conseil = (
            "🚨 <strong>Débit très élevé</strong> - Vérifiez les vannes, augmentez "
            "l'évacuation et déclenchez les alertes de crue immédiatement."
        )
    elif debit > 50:
        conseil = (
            "⚠️ <strong>Débit modéré</strong> - Surveillez les relevés toutes les heures, "
            "ajustez les vannes et préparez les alertes si le débit continue d'augmenter."
        )
    else:
        conseil = (
            "✅ <strong>Débit normal</strong> - Les opérations se poursuivent normalement. "
            "Continuez le suivi régulier de la situation."
        )

    html = f"""
    <div class="conseil-box">
        {conseil}
    </div>
    """
    return HTMLResponse(content=html)

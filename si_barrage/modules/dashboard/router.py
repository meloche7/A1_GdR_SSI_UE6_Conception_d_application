# Endpoints de l'API pour le dashboard
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ...db import get_db
from . import services
from ..meteo import services as meteo_services

router = APIRouter()


def _render_graph_with_axes(values_real, values_prev, width=800, height=400, y_label="Débit (m³/s)") -> str:
    """
    Retourne un graphique SVG professionnel avec axes X/Y comparant 2 séries de données.
    """
    if not values_real or not values_prev:
        return "<div style='text-align:center;color:#666;'>Aucune donnée disponible</div>"
    
    # Normaliser les deux séries ensemble
    all_values = values_real + values_prev
    min_v = min(all_values)
    max_v = max(all_values)
    span = max_v - min_v if max_v > min_v else 1
    
    # Dimensions
    margin_left = 70
    margin_right = 30
    margin_top = 40
    margin_bottom = 80
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    
    # Générer les points
    def get_points(values):
        points = []
        for i, v in enumerate(values):
            x = margin_left + (i / (len(values) - 1)) * plot_width if len(values) > 1 else margin_left + plot_width / 2
            y = margin_top + plot_height - ((v - min_v) / span) * plot_height
            points.append((x, y, v))
        return points
    
    points_real = get_points(values_real)
    points_prev = get_points(values_prev)
    
    # Polylines
    def create_polyline(points, color):
        coords = " ".join([f"{x},{y}" for x, y, _ in points])
        return f'<polyline fill="none" stroke="{color}" stroke-width="3" stroke-linejoin="round" stroke-linecap="round" points="{coords}" />'
    
    polyline_real = create_polyline(points_real, "#0099ff")
    polyline_prev = create_polyline(points_prev, "#f59e0b")
    
    # Axes
    x_axis = f'<line x1="{margin_left}" y1="{margin_top + plot_height}" x2="{width - margin_right}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="2"/>'
    y_axis = f'<line x1="{margin_left}" y1="{margin_top}" x2="{margin_left}" y2="{margin_top + plot_height}" stroke="#333" stroke-width="2"/>'
    
    # Graduations Y
    y_ticks = ""
    for i in range(5):
        y_val = min_v + (i / 4) * span
        y_pos = margin_top + plot_height - (i / 4) * plot_height
        y_ticks += f'<line x1="{margin_left - 8}" y1="{y_pos}" x2="{margin_left}" y2="{y_pos}" stroke="#333" stroke-width="1"/>'
        y_ticks += f'<text x="{margin_left - 12}" y="{y_pos + 4}" font-size="11" text-anchor="end" fill="#666">{y_val:.0f}</text>'
    
    # Graduations X
    x_ticks = ""
    num_ticks = min(len(values_real), 8)
    for i in range(num_ticks):
        x_idx = int((i / (num_ticks - 1)) * (len(values_real) - 1)) if num_ticks > 1 else 0
        x_pos = margin_left + (x_idx / (len(values_real) - 1)) * plot_width if len(values_real) > 1 else margin_left + plot_width / 2
        x_ticks += f'<line x1="{x_pos}" y1="{margin_top + plot_height}" x2="{x_pos}" y2="{margin_top + plot_height + 8}" stroke="#333" stroke-width="1"/>'
        x_ticks += f'<text x="{x_pos}" y="{margin_top + plot_height + 25}" font-size="11" text-anchor="middle" fill="#666">{x_idx}</text>'
    
    # Labels axes
    y_label_text = f'<text x="20" y="{margin_top + plot_height / 2}" font-size="12" fill="#666" text-anchor="middle" transform="rotate(-90 20 {margin_top + plot_height / 2})">{y_label}</text>'
    x_label_text = f'<text x="{margin_left + plot_width / 2}" y="{margin_top + plot_height + 65}" font-size="12" text-anchor="middle" fill="#666">Temps (indices)</text>'
    
    svg = f"""
    <svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="{width}" height="{height}" fill="white" stroke="#eee" stroke-width="1"/>
        {y_ticks}
        {x_ticks}
        {x_axis}
        {y_axis}
        {polyline_real}
        {polyline_prev}
        {y_label_text}
        {x_label_text}
    </svg>
    """
    
    return svg


@router.get("/api/debit-reel", response_class=HTMLResponse)
async def get_debit_reel_html(db: Session = Depends(get_db)):
    """Retourne le débit en temps réel (dernier relevé)."""
    releves = meteo_services.get_latest_releves(db, limit=1)
    if not releves:
        return HTMLResponse(content="<div style='text-align:center;color:#999;'>Aucun relevé</div>")

    last = releves[0]
    html = f"""
    <div class="metric-value">{last['debit_riviere_m3s']:.1f}</div>
    <div class="metric-unit">m³/s</div>
    """
    return HTMLResponse(content=html)


@router.get("/api/pluie-actuelle", response_class=HTMLResponse)
async def get_pluie_actuelle_html(db: Session = Depends(get_db)):
    """Retourne la pluie actuelle (dernier relevé)."""
    releves = meteo_services.get_latest_releves(db, limit=1)
    if not releves:
        return HTMLResponse(content="<div style='text-align:center;color:#999;'>Aucun relevé</div>")

    last = releves[0]
    html = f"""
    <div class="metric-value">{last['pluviometrie_mm']:.1f}</div>
    <div class="metric-unit">mm</div>
    """
    return HTMLResponse(content=html)


@router.get("/api/tendance", response_class=HTMLResponse)
async def get_tendance_html(db: Session = Depends(get_db)):
    """Retourne la tendance du débit."""
    releves = meteo_services.get_latest_releves(db, limit=2)
    if len(releves) < 2:
        tendance = "➡️ Stable"
    else:
        dernier = releves[0]['debit_riviere_m3s']
        precedent = releves[1]['debit_riviere_m3s']
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


@router.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """
    Page principale du dashboard météo avec HTMX.
    """
    html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Météo - SI Barrage</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', sans-serif;
            background: linear-gradient(135deg, #0f3460 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        h1 {
            color: white;
            font-size: 2.8rem;
            text-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .status-indicator {
            display: flex;
            align-items: center;
            gap: 10px;
            background: rgba(255, 255, 255, 0.1);
            padding: 10px 20px;
            border-radius: 50px;
            color: white;
            font-size: 0.9rem;
        }
        
        .status-dot {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .top-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            border-radius: 16px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            text-align: center;
            min-height: 180px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        
        .metric-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
        }
        
        .metric-title {
            font-size: 0.9rem;
            color: #888;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }
        
        .metric-value {
            font-size: 2.4rem;
            color: #0099ff;
            font-weight: 800;
            font-variant-numeric: tabular-nums;
        }
        
        .metric-unit {
            font-size: 0.8rem;
            color: #666;
            margin-top: 5px;
        }
        
        .bottom-row {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            position: relative;
            overflow: hidden;
        }
        
        .card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #00d4ff, #0099ff);
        }
        
        .card:hover {
            transform: translateY(-8px);
            box-shadow: 0 16px 48px rgba(0, 0, 0, 0.2);
        }
        
        .card-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 25px;
        }
        
        .card-icon {
            font-size: 1.8rem;
        }
        
        .card-title {
            font-size: 1.2rem;
            color: #333;
            font-weight: 700;
            letter-spacing: -0.5px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        thead {
            background: linear-gradient(135deg, #f0f4f8 0%, #f8fbff 100%);
        }
        
        th {
            text-align: left;
            padding: 14px;
            font-weight: 700;
            color: #0f3460;
            border-bottom: 2px solid #e0e7ff;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        td {
            padding: 14px;
            border-bottom: 1px solid #f0f0f0;
            color: #555;
            font-size: 0.95rem;
        }
        
        tbody tr {
            transition: all 0.2s ease;
        }
        
        tbody tr:hover {
            background: linear-gradient(90deg, #f0f4f8 0%, #f8fbff 100%);
        }
        
        .estimation-box {
            background: linear-gradient(135deg, #f0f4f8 0%, #f8fbff 100%);
            padding: 20px;
            border-radius: 12px;
            margin-bottom: 20px;
        }
        
        .conseil-box {
            background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #f59e0b;
            line-height: 1.6;
            color: #333;
            font-size: 0.95rem;
        }
        
        .loading {
            text-align: center;
            padding: 40px 20px;
            color: #999;
        }
        
        .spinner {
            border: 3px solid #f0f0f0;
            border-top: 3px solid #0099ff;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            animation: spin 0.8s linear infinite;
            margin: 0 auto 10px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .legend {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            padding-top: 15px;
            border-top: 1px solid #eee;
            flex-wrap: wrap;
        }
        
        .legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 0.9rem;
            color: #666;
        }
        
        .legend-color {
            width: 16px;
            height: 3px;
            border-radius: 2px;
        }
        
        .color-real { background: #0099ff; }
        .color-prev { background: #f59e0b; }
        
        svg {
            max-width: 100%;
            height: auto;
            display: block;
        }
        
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                gap: 15px;
            }
            
            .top-row {
                grid-template-columns: 1fr;
            }
            
            .bottom-row {
                grid-template-columns: 1fr;
            }
            
            h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🌦️ Dashboard Météo</h1>
            <div class="status-indicator">
                <div class="status-dot"></div>
                Système en ligne
            </div>
        </div>
        
        <!-- Première ligne : 3 colonnes -->
        <div class="top-row">
            <!-- Débit en temps réel -->
            <div class="metric-card">
                <div class="metric-title">Débit en temps réel</div>
                <div id="debit-reel" 
                     hx-get="/dashboard/api/debit-reel" 
                     hx-trigger="load, every 30s"
                     hx-swap="innerHTML">
                    <div class="loading">
                        <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
                    </div>
                </div>
            </div>

            <!-- Historique des débits -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📋</span>
                    <h2 class="card-title">Historique des débits</h2>
                </div>
                <div id="historique-debits" 
                     hx-get="/dashboard/api/historique-debits" 
                     hx-trigger="load, every 60s"
                     hx-swap="innerHTML">
                    <div class="loading">
                        <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
                    </div>
                </div>
            </div>

            <!-- Graphique des débits + prévisions -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">📊</span>
                    <h2 class="card-title">Graphique débits + prévisions</h2>
                </div>
                <div id="graphique-debits" 
                     hx-get="/dashboard/api/debit-graph" 
                     hx-trigger="load, every 30s"
                     hx-swap="innerHTML">
                    <div class="loading">
                        <div class="spinner"></div>
                        Chargement...
                    </div>
                </div>
            </div>
        </div>

        <!-- Deuxième ligne : 4 colonnes (2 colonnes x 2) -->
        <div class="bottom-row">
            <!-- Historique des pluies -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">💧</span>
                    <h2 class="card-title">Historique pluies</h2>
                </div>
                <div id="historique-pluie" 
                     hx-get="/dashboard/api/historique-pluie" 
                     hx-trigger="load, every 60s"
                     hx-swap="innerHTML">
                    <div class="loading">
                        <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
                    </div>
                </div>
            </div>

            <!-- Graphique pluie + prévision -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">🌧️</span>
                    <h2 class="card-title">Graphique pluie + prévision</h2>
                </div>
                <div id="graphique-pluie" 
                     hx-get="/dashboard/api/pluie-graph" 
                     hx-trigger="load, every 30s"
                     hx-swap="innerHTML">
                    <div class="loading">
                        <div class="spinner"></div>
                        Chargement...
                    </div>
                </div>
            </div>

            <!-- Estimation crue rivière -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">⚠️</span>
                    <h2 class="card-title">Estimation crue rivière</h2>
                </div>
                <div id="estimation-crue" 
                     hx-get="/dashboard/api/estimation-crue" 
                     hx-trigger="load, every 60s"
                     hx-swap="innerHTML">
                    <div class="loading">
                        <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
                    </div>
                </div>
            </div>

            <!-- Conseil gestion opération -->
            <div class="card">
                <div class="card-header">
                    <span class="card-icon">💡</span>
                    <h2 class="card-title">Conseil gestion opération</h2>
                </div>
                <div id="conseils-operation" 
                     hx-get="/dashboard/api/conseils-operation" 
                     hx-trigger="load, every 60s"
                     hx-swap="innerHTML">
                    <div class="loading">
                        <div class="spinner" style="width: 16px; height: 16px; border-width: 2px;"></div>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


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
    releves = meteo_services.get_latest_releves(db, limit=15)
    previsions = meteo_services.get_latest_previsions(db, limit=15)

    values_reel = [r['debit_riviere_m3s'] for r in releves]
    values_prev = [p['debit_riviere_m3s_prevu'] for p in previsions]

    # Assurer que les deux listes ont la même longueur
    max_len = max(len(values_reel), len(values_prev))
    if len(values_reel) < max_len:
        values_reel += [values_reel[-1]] * (max_len - len(values_reel)) if values_reel else [0] * max_len
    if len(values_prev) < max_len:
        values_prev += [values_prev[-1]] * (max_len - len(values_prev)) if values_prev else [0] * max_len

    graph = _render_graph_with_axes(values_reel, values_prev, y_label="Débit (m³/s)")
    
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
    releves = meteo_services.get_latest_releves(db, limit=10)
    rows = ""
    for r in releves:
        rows += f"""
        <tr>
            <td>{r['date']}</td>
            <td>{r['debit_riviere_m3s']:.1f}</td>
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
    releves = meteo_services.get_latest_releves(db, limit=10)
    rows = ""
    for r in releves:
        rows += f"""
        <tr>
            <td>{r['date']}</td>
            <td>{r['pluviometrie_mm']:.1f}</td>
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
    releves = meteo_services.get_latest_releves(db, limit=15)
    previsions = meteo_services.get_latest_previsions(db, limit=15)

    values_reel = [r['pluviometrie_mm'] for r in releves]
    values_prev = [p['pluviometrie_mm_prevue'] for p in previsions]

    # Assurer que les deux listes ont la même longueur
    max_len = max(len(values_reel), len(values_prev))
    if len(values_reel) < max_len:
        values_reel += [values_reel[-1]] * (max_len - len(values_reel)) if values_reel else [0] * max_len
    if len(values_prev) < max_len:
        values_prev += [values_prev[-1]] * (max_len - len(values_prev)) if values_prev else [0] * max_len

    graph = _render_graph_with_axes(values_reel, values_prev, y_label="Pluie (mm)")
    
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
    releves = meteo_services.get_latest_releves(db, limit=1)
    previsions = meteo_services.get_latest_previsions(db, limit=3)

    if not releves:
        return HTMLResponse(content="<div style='text-align:center;color:#999;'>Aucune donnée</div>")

    dernier_debit = releves[0]['debit_riviere_m3s']
    prochains = [p['debit_riviere_m3s_prevu'] for p in previsions]
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
    releves = meteo_services.get_latest_releves(db, limit=1)
    if not releves:
        return HTMLResponse(content="<div style='text-align:center;color:#999;'>Aucune donnée</div>")

    debit = releves[0]['debit_riviere_m3s']
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

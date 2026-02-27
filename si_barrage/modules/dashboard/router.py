# Endpoints de l'API pour le dashboard
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ...db import get_db
from . import services

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """
    Page principale du dashboard avec HTMX.
    """
    html_content = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard SI Barrage</title>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        h1 {
            color: white;
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .dashboard-grid {
            display: grid;
            grid-template-columns: 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }
        
        @media (min-width: 768px) {
            .dashboard-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }
        
        .card:hover {
            transform: translateY(-5px);
        }
        
        .card-title {
            font-size: 1.2rem;
            color: #333;
            margin-bottom: 15px;
            font-weight: 600;
        }
        
        .metric {
            font-size: 3rem;
            color: #667eea;
            font-weight: bold;
            text-align: center;
            padding: 20px 0;
        }
        
        .metric-label {
            text-align: center;
            color: #666;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .table-card {
            grid-column: 1 / -1;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        thead {
            background: #f8f9fa;
        }
        
        th {
            text-align: left;
            padding: 12px;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #dee2e6;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #e9ecef;
            color: #495057;
        }
        
        tr:hover {
            background: #f8f9fa;
        }
        
        .status-badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 500;
        }
        
        .status-en-cours {
            background: #fff3cd;
            color: #856404;
        }
        
        .status-planifie {
            background: #cce5ff;
            color: #004085;
        }
        
        .status-termine {
            background: #d4edda;
            color: #155724;
        }
        
        .status-urgent {
            background: #f8d7da;
            color: #721c24;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            color: #666;
        }
        
        .htmx-indicator {
            display: none;
        }
        
        .htmx-request .htmx-indicator {
            display: inline;
        }
        
        .htmx-request.htmx-indicator {
            display: inline;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🏭 Dashboard SI Barrage</h1>
        
        <div class="dashboard-grid">
            <!-- Production Moyenne -->
            <div class="card">
                <h2 class="card-title">Production Moyenne</h2>
                <div id="mean-production" 
                     hx-get="/dashboard/api/mean-production" 
                     hx-trigger="load, every 30s"
                     hx-swap="innerHTML">
                    <div class="loading">Chargement...</div>
                </div>
            </div>
            
            <!-- Placeholder pour futur indicateur -->
            <div class="card">
                <h2 class="card-title">Statut Général</h2>
                <div class="metric" style="font-size: 2rem; color: #28a745;">
                    ✓ Opérationnel
                </div>
                <div class="metric-label">Système</div>
            </div>
            
            <!-- Dernières Maintenances -->
            <div class="card table-card">
                <h2 class="card-title">Dernières Maintenances</h2>
                <div id="maintenance-table" 
                     hx-get="/dashboard/api/last-maintenance" 
                     hx-trigger="load, every 60s"
                     hx-swap="innerHTML">
                    <div class="loading">Chargement des données...</div>
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
    <div class="metric">{mean_prod}</div>
    <div class="metric-label">MWh</div>
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

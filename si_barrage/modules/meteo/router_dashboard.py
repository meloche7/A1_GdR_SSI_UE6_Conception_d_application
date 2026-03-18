# Endpoints de l'API pour le dashboard
from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from ...db import get_db
from ..meteo import services as meteo_services
from . import services

router = APIRouter()


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
        </div>
        
        <!-- Première ligne : 3 colonnes -->
        <div class="top-row">
            <!-- Débit en temps réel -->
            <div class="metric-card">
                <div class="metric-title">Débit en temps réel</div>
                <div id="debit-reel" 
                     hx-get="/meteo/api/debit-reel" 
                     hx-trigger="load, every 10s"
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
                     hx-get="/meteo/api/historique-debits" 
                     hx-trigger="load, every 10s"
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
                    <h2 class="card-title">Graphique débits et prévisions</h2>
                </div>
                <div id="graphique-debits" 
                     hx-get="/meteo/api/debit-graph" 
                     hx-trigger="load, every 10s"
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
                     hx-get="/meteo/api/historique-pluie" 
                     hx-trigger="load, every 10s"
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
                    <h2 class="card-title">Graphique pluie et prévision</h2>
                </div>
                <div id="graphique-pluie" 
                     hx-get="/meteo/api/pluie-graph" 
                     hx-trigger="load, every 10s"
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
                     hx-get="/meteo/api/estimation-crue" 
                     hx-trigger="load, every 10s"
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
                     hx-get="/meteo/api/conseils-operation" 
                     hx-trigger="load, every 10s"
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

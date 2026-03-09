"""
API FastAPI pour gestion de barrage avec prévisions météo
Base de données: SQLAlchemy (SQLite)
Dashboard: Intégré en HTML/CSS/JS
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from datetime import datetime, timedelta
import logging
import os

# ============= CONFIGURATION =============

DATABASE_URL = "sqlite:///./barrage.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============= MODÈLES DB (SQLAlchemy) =============

class MeteoPrevisionsDB(Base):
    __tablename__ = "meteo_previsions"
    
    id = Column(Integer, primary_key=True, index=True)
    date_prevision = Column(String, index=True)
    date_creation = Column(String)
    debit_riviere_m3s_prevu = Column(Float)
    pluviometrie_mm_prevue = Column(Float)

class AlerteSystemeDB(Base):
    __tablename__ = "alertes_systeme"
    
    id = Column(Integer, primary_key=True, index=True)
    type_alerte = Column(String)
    niveau_severite = Column(String)
    message = Column(String)
    date_creation = Column(String)
    date_prévue = Column(String)
    recommandations = Column(String)
    traitée = Column(Integer, default=0)

class ParametreAlerteDB(Base):
    __tablename__ = "parametres_alerte"
    
    clé = Column(String, primary_key=True, index=True)
    valeur = Column(String)
    description = Column(String)

# ============= MODÈLES PYDANTIC =============

class PrevisionMeteo(BaseModel):
    date_prevision: str
    date_creation: str
    debit_riviere_m3s_prevu: float
    pluviometrie_mm_prevue: float
    
    class Config:
        from_attributes = True

class AlerteSysteme(BaseModel):
    id: int = None
    type_alerte: str
    niveau_severite: str
    message: str
    date_creation: str
    date_prévue: str
    recommandations: list = []
    
    class Config:
        from_attributes = True

class ResumePrevisions(BaseModel):
    pluviometrie_moyenne: float
    pluviometrie_max: float
    debit_moyen: float
    debit_max: float
    alerte_majeure: AlerteSysteme = None

# ============= CRÉATION APP =============

app = FastAPI(
    title="API Gestion Barrage",
    description="Système de gestion et prévisions pour barrages",
    version="1.0.0"
)

# ============= INITIALISATION BD =============

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_default_params(db: Session):
    """Initialise les paramètres par défaut"""
    defaults = [
        ("DEBIT_CRITIQUE_M3S", "500", "Débit critique (m³/s)"),
        ("PLUVIO_ALERTE_MM", "50", "Pluviométrie d'alerte (mm)"),
        ("PLUVIO_CRITIQUE_MM", "100", "Pluviométrie critique (mm)"),
        ("DEBIT_FAIBLE_M3S", "50", "Débit faible/sécheresse (m³/s)"),
    ]
    
    for cle, val, desc in defaults:
        existing = db.query(ParametreAlerteDB).filter(ParametreAlerteDB.clé == cle).first()
        if not existing:
            db.add(ParametreAlerteDB(clé=cle, valeur=val, description=desc))
    db.commit()

@app.on_event("startup")
def startup():
    """À la démarrage de l'app"""
    db = SessionLocal()
    init_default_params(db)
    db.close()
    logger.info("✅ Application démarrée - BD initialisée")

# ============= ENDPOINTS API =============

@app.get("/")
async def root():
    """Redirection vers le dashboard"""
    return {"message": "API Barrage - Voir /dashboard ou /docs"}

@app.get("/api/health")
async def health(db: Session = None):
    """Health check"""
    try:
        db = SessionLocal()
        count = db.query(MeteoPrevisionsDB).count()
        db.close()
        return {
            "status": "healthy",
            "database": "connected",
            "previsions_count": count
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")

@app.get("/api/previsions", response_model=list[PrevisionMeteo])
async def get_previsions(
    jours: int = Query(10, ge=1, le=30),
    db: Session = None
):
    """Récupère les prévisions"""
    db = SessionLocal()
    try:
        date_debut = datetime.now().date().isoformat()
        date_fin = (datetime.now() + timedelta(days=jours)).date().isoformat()
        
        previsions = db.query(MeteoPrevisionsDB).filter(
            MeteoPrevisionsDB.date_prevision >= date_debut,
            MeteoPrevisionsDB.date_prevision <= date_fin
        ).order_by(MeteoPrevisionsDB.date_prevision).all()
        
        if not previsions:
            raise HTTPException(status_code=404, detail="Aucune prévision")
        
        return previsions
    finally:
        db.close()

@app.get("/api/previsions/resumes", response_model=ResumePrevisions)
async def get_resume(jours: int = Query(10, ge=1, le=30), db: Session = None):
    """Résumé statistique des prévisions"""
    db = SessionLocal()
    try:
        date_debut = datetime.now().date().isoformat()
        date_fin = (datetime.now() + timedelta(days=jours)).date().isoformat()
        
        previsions = db.query(MeteoPrevisionsDB).filter(
            MeteoPrevisionsDB.date_prevision >= date_debut,
            MeteoPrevisionsDB.date_prevision <= date_fin
        ).all()
        
        if not previsions:
            raise HTTPException(status_code=404, detail="Données insuffisantes")
        
        debits = [p.debit_riviere_m3s_prevu for p in previsions]
        pluvios = [p.pluviometrie_mm_prevue for p in previsions]
        
        # Récupérer alerte majeure
        alerte = db.query(AlerteSystemeDB).filter(
            AlerteSystemeDB.traitée == 0
        ).order_by(AlerteSystemeDB.date_creation.desc()).first()
        
        alerte_obj = None
        if alerte:
            alerte_obj = AlerteSysteme(
                id=alerte.id,
                type_alerte=alerte.type_alerte,
                niveau_severite=alerte.niveau_severite,
                message=alerte.message,
                date_creation=alerte.date_creation,
                date_prévue=alerte.date_prévue,
                recommandations=alerte.recommandations.split("|") if alerte.recommandations else []
            )
        
        return ResumePrevisions(
            pluviometrie_moyenne=sum(pluvios) / len(pluvios) if pluvios else 0,
            pluviometrie_max=max(pluvios) if pluvios else 0,
            debit_moyen=sum(debits) / len(debits) if debits else 0,
            debit_max=max(debits) if debits else 0,
            alerte_majeure=alerte_obj
        )
    finally:
        db.close()

@app.get("/api/alertes", response_model=list[AlerteSysteme])
async def get_alertes(
    non_traitees_seulement: bool = False,
    db: Session = None
):
    """Récupère les alertes"""
    db = SessionLocal()
    try:
        query = db.query(AlerteSystemeDB)
        
        if non_traitees_seulement:
            query = query.filter(AlerteSystemeDB.traitée == 0)
        
        alertes = query.order_by(AlerteSystemeDB.date_creation.desc()).limit(50).all()
        
        result = []
        for a in alertes:
            result.append(AlerteSysteme(
                id=a.id,
                type_alerte=a.type_alerte,
                niveau_severite=a.niveau_severite,
                message=a.message,
                date_creation=a.date_creation,
                date_prévue=a.date_prévue,
                recommandations=a.recommandations.split("|") if a.recommandations else []
            ))
        
        return result
    finally:
        db.close()

@app.post("/api/alertes/creer")
async def creer_alerte(alerte: AlerteSysteme, db: Session = None):
    """Crée une nouvelle alerte"""
    db = SessionLocal()
    try:
        rec_str = "|".join(alerte.recommandations) if alerte.recommandations else ""
        
        new_alerte = AlerteSystemeDB(
            type_alerte=alerte.type_alerte,
            niveau_severite=alerte.niveau_severite,
            message=alerte.message,
            date_creation=alerte.date_creation,
            date_prévue=alerte.date_prévue,
            recommandations=rec_str
        )
        
        db.add(new_alerte)
        db.commit()
        db.refresh(new_alerte)
        
        logger.info(f"Alerte créée: {alerte.type_alerte}")
        return {"id": new_alerte.id, "status": "created"}
    finally:
        db.close()

@app.put("/api/alertes/{alerte_id}/marquer-traitee")
async def marquer_alerte_traitee(alerte_id: int, db: Session = None):
    """Marque une alerte comme traitée"""
    db = SessionLocal()
    try:
        alerte = db.query(AlerteSystemeDB).filter(AlerteSystemeDB.id == alerte_id).first()
        if not alerte:
            raise HTTPException(status_code=404, detail="Alerte non trouvée")
        
        alerte.traitée = 1
        db.commit()
        
        return {"status": "marked_as_treated"}
    finally:
        db.close()

@app.get("/api/parametres")
async def get_parametres(db: Session = None):
    """Récupère les paramètres"""
    db = SessionLocal()
    try:
        params = db.query(ParametreAlerteDB).all()
        
        result = {}
        for p in params:
            result[p.clé] = {
                "valeur": float(p.valeur),
                "description": p.description
            }
        
        return result
    finally:
        db.close()

@app.put("/api/parametres/{cle}")
async def update_parametre(cle: str, valeur: float, db: Session = None):
    """Met à jour un paramètre"""
    db = SessionLocal()
    try:
        param = db.query(ParametreAlerteDB).filter(ParametreAlerteDB.clé == cle).first()
        if not param:
            raise HTTPException(status_code=404, detail="Paramètre non trouvé")
        
        param.valeur = str(valeur)
        db.commit()
        
        logger.info(f"Paramètre {cle} mis à jour à {valeur}")
        return {"status": "updated"}
    finally:
        db.close()

@app.post("/api/previsions/importer")
async def importer_previsions(previsions: list[PrevisionMeteo], db: Session = None):
    """Importe des prévisions"""
    db = SessionLocal()
    try:
        for prev in previsions:
            new_prev = MeteoPrevisionsDB(
                date_prevision=prev.date_prevision,
                date_creation=prev.date_creation,
                debit_riviere_m3s_prevu=prev.debit_riviere_m3s_prevu,
                pluviometrie_mm_prevue=prev.pluviometrie_mm_prevue
            )
            db.add(new_prev)
        
        db.commit()
        logger.info(f"{len(previsions)} prévisions importées")
        return {"count": len(previsions), "status": "imported"}
    finally:
        db.close()

# ============= DASHBOARD HTML INTERNE =============

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Barrage Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
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
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        
        .subtitle {
            color: #666;
            font-size: 14px;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .metric-card {
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .metric-card h3 {
            color: #666;
            font-size: 14px;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-value {
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }
        
        .metric-unit {
            font-size: 12px;
            color: #999;
            margin-top: 5px;
        }
        
        .alert-box {
            background: #fee;
            border-left: 4px solid #f44;
            padding: 20px;
            border-radius: 5px;
            margin-bottom: 20px;
        }
        
        .alert-box.success {
            background: #efe;
            border-left-color: #4f4;
        }
        
        .alert-box h4 {
            margin-bottom: 10px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            background: white;
            padding: 15px;
            border-radius: 10px;
        }
        
        .tab-btn {
            padding: 10px 20px;
            background: #f0f0f0;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 500;
            transition: all 0.3s;
        }
        
        .tab-btn.active {
            background: #667eea;
            color: white;
        }
        
        .tab-content {
            display: none;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .tab-content.active {
            display: block;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin-bottom: 30px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            background: #f5f5f5;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            border-bottom: 2px solid #ddd;
        }
        
        td {
            padding: 12px 15px;
            border-bottom: 1px solid #eee;
        }
        
        tr:hover {
            background: #f9f9f9;
        }
        
        button {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 500;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #5568d3;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #999;
        }
        
        .error {
            color: #d32f2f;
            padding: 20px;
            background: #ffebee;
            border-radius: 5px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🏔️ Barrage Dashboard</h1>
            <p class="subtitle">Système de gestion et prévisions météo en temps réel</p>
        </header>
        
        <div id="alerts"></div>
        
        <div class="metrics" id="metrics">
            <div class="loading">Chargement des données...</div>
        </div>
        
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('overview')">📊 Vue d'ensemble</button>
            <button class="tab-btn" onclick="switchTab('pluie')">☔ Pluviométrie</button>
            <button class="tab-btn" onclick="switchTab('debit')">💧 Débits</button>
            <button class="tab-btn" onclick="switchTab('table')">📜 Tableau</button>
        </div>
        
        <div id="overview" class="tab-content active">
            <div class="chart-container">
                <canvas id="chartCombined"></canvas>
            </div>
        </div>
        
        <div id="pluie" class="tab-content">
            <div class="chart-container">
                <canvas id="chartPluie"></canvas>
            </div>
        </div>
        
        <div id="debit" class="tab-content">
            <div class="chart-container">
                <canvas id="chartDebit"></canvas>
            </div>
        </div>
        
        <div id="table" class="tab-content">
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Débit (m³/s)</th>
                        <th>Pluviométrie (mm)</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr><td colspan="3" class="loading">Chargement...</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        let previsions = [];
        let charts = {};
        
        async function loadData() {
            try {
                const response = await fetch('/api/previsions?jours=10');
                if (!response.ok) throw new Error('Erreur réseau');
                
                previsions = await response.json();
                await loadResume();
                updateCharts();
                updateTable();
            } catch (error) {
                console.error('Erreur:', error);
                document.getElementById('metrics').innerHTML = 
                    '<div class="error">Erreur lors du chargement des données</div>';
            }
        }
        
        async function loadResume() {
            try {
                const response = await fetch('/api/previsions/resumes?jours=10');
                const data = await response.json();
                
                document.getElementById('metrics').innerHTML = `
                    <div class="metric-card">
                        <h3>Pluviométrie Moyenne</h3>
                        <div class="metric-value">${data.pluviometrie_moyenne.toFixed(1)}</div>
                        <div class="metric-unit">mm</div>
                    </div>
                    <div class="metric-card">
                        <h3>Pluviométrie Max</h3>
                        <div class="metric-value">${data.pluviometrie_max.toFixed(1)}</div>
                        <div class="metric-unit">mm</div>
                    </div>
                    <div class="metric-card">
                        <h3>Débit Moyen</h3>
                        <div class="metric-value">${data.debit_moyen.toFixed(1)}</div>
                        <div class="metric-unit">m³/s</div>
                    </div>
                    <div class="metric-card">
                        <h3>Débit Max</h3>
                        <div class="metric-value">${data.debit_max.toFixed(1)}</div>
                        <div class="metric-unit">m³/s</div>
                    </div>
                `;
                
                // Afficher alerte si existe
                if (data.alerte_majeure) {
                    const alerte = data.alerte_majeure;
                    const couleur = alerte.niveau_severite === 'CRITIQUE' ? '' : 'success';
                    document.getElementById('alerts').innerHTML = `
                        <div class="alert-box ${couleur}">
                            <h4>⚠️ ${alerte.type_alerte}</h4>
                            <p>${alerte.message}</p>
                            <small>Prévue: ${alerte.date_prévue}</small>
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Erreur résumé:', error);
            }
        }
        
        function updateCharts() {
            const labels = previsions.map(p => {
                const date = new Date(p.date_prevision);
                return date.toLocaleDateString('fr-FR', {month: 'short', day: 'numeric'});
            });
            
            const debits = previsions.map(p => parseFloat(p.debit_riviere_m3s_prevu));
            const pluvios = previsions.map(p => parseFloat(p.pluviometrie_mm_prevue));
            
            // Vue d'ensemble
            if (charts.combined) charts.combined.destroy();
            charts.combined = new Chart(document.getElementById('chartCombined'), {
                type: 'line',
                data: {
                    labels,
                    datasets: [
                        {
                            label: 'Débit (m³/s)',
                            data: debits,
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Pluviométrie (mm)',
                            data: pluvios,
                            borderColor: '#764ba2',
                            backgroundColor: 'rgba(118, 75, 162, 0.1)',
                            tension: 0.4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {mode: 'index', intersect: false},
                    scales: {
                        y: {position: 'left', title: {display: true, text: 'Débit (m³/s)'}},
                        y1: {position: 'right', title: {display: true, text: 'Pluviométrie (mm)'}}
                    }
                }
            });
            
            // Pluviométrie
            if (charts.pluie) charts.pluie.destroy();
            charts.pluie = new Chart(document.getElementById('chartPluie'), {
                type: 'bar',
                data: {
                    labels,
                    datasets: [{
                        label: 'Pluviométrie (mm)',
                        data: pluvios,
                        backgroundColor: '#764ba2'
                    }]
                },
                options: {responsive: true, maintainAspectRatio: false}
            });
            
            // Débits
            if (charts.debit) charts.debit.destroy();
            charts.debit = new Chart(document.getElementById('chartDebit'), {
                type: 'line',
                data: {
                    labels,
                    datasets: [{
                        label: 'Débit (m³/s)',
                        data: debits,
                        borderColor: '#667eea',
                        backgroundColor: 'rgba(102, 126, 234, 0.1)',
                        tension: 0.4
                    }]
                },
                options: {responsive: true, maintainAspectRatio: false}
            });
        }
        
        function updateTable() {
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = previsions.map(p => `
                <tr>
                    <td>${p.date_prevision}</td>
                    <td>${parseFloat(p.debit_riviere_m3s_prevu).toFixed(1)}</td>
                    <td>${parseFloat(p.pluviometrie_mm_prevue).toFixed(1)}</td>
                </tr>
            `).join('');
        }
        
        function switchTab(tab) {
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            document.getElementById(tab).classList.add('active');
            event.target.classList.add('active');
            
            // Redessiner les graphiques
            setTimeout(() => {
                Object.values(charts).forEach(chart => chart?.resize());
            }, 100);
        }
        
        // Charger les données au démarrage et toutes les minutes
        loadData();
        setInterval(loadData, 60000);
    </script>
</body>
</html>
"""

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Page du dashboard"""
    return DASHBOARD_HTML

# ============= DÉMARRAGE =============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

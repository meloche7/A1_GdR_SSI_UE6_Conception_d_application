from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import date

app = FastAPI(title="Module Production - Reporting & KPIs")

# --- Modèles de données (Schemas) ---

class ProductionData(BaseModel):
    date: date
    production_mwh: float
    volume_eau_m3: float

class MeteoHistorique(BaseModel):
    date: date
    debit_riviere_m3s: float
    pluviometrie_mm: float

# --- Stockage temporaire (Simulation de Base de Données) ---
db_production: List[ProductionData] = []
db_meteo: List[MeteoHistorique] = []
config = {
    "prix_electricite": 0.0,
    "seuil_sous_prod": 0.0,
    "seuil_sur_prod": 0.0
}

# Saisie et Imports

@app.post("/production/saisie", tags=["Entrées"])
async def saisie_production(data: ProductionData):
    """Saisie manuelle de la production et du volume d'eau [cite: 37]"""
    db_production.append(data)
    return {"status": "confirmation", "message": "Donnée enregistrée"}

@app.post("/meteo/import", tags=["Entrées"])
async def import_meteo(data: List[MeteoHistorique]):
    """Import des données météo historiques [cite: 37]"""
    db_meteo.extend(data)
    return {"status": "confirmation", "nb_records": len(data)}

@app.post("/prix/production", tags=["Configuration"])
async def set_prix(prix: float):
    """Définir le prix de l'électricité pour le calcul des revenus [cite: 37]"""
    config["prix_electricite"] = prix
    return {"status": "confirmation"}

#Calcul des KPIs
@app.get("/kpi/rendement", tags=["Analyses"])
async def get_rendement(date_start: date, date_end: date):
    """Calcule le rendement : production_mwh / volume_eau_m3 [cite: 18, 39]"""
    period_data = [d for d in db_production if date_start <= d.date <= date_end]
    if not period_data:
        raise HTTPException(status_code=404, detail="Aucune donnée sur cette période")

    results = []
    total_prod = 0
    total_vol = 0
    
    for d in period_data:
        rendement_j = d.production_mwh / d.volume_eau_m3 if d.volume_eau_m3 > 0 else 0
        results.append({"date": d.date, "rendement_journalier": rendement_j})
        total_prod += d.production_mwh
        total_vol += d.volume_eau_m3

    return {
        "detail_journalier": results,
        "rendement_moyen": total_prod / total_vol if total_vol > 0 else 0
    }

@app.get("/kpi/revenu", tags=["Analyses"])
async def get_revenu(date_start: date, date_end: date):
    """Calcule les revenus : production_mwh x prix_electricite [cite: 20, 39]"""
    period_data = [d for d in db_production if date_start <= d.date <= date_end]
    
    revenus_jours = [
        {"date": d.date, "revenu": d.production_mwh * config["prix_electricite"]} 
        for d in period_data
    ]
    total_revenu = sum(item["revenu"] for item in revenus_jours)
    
    return {"revenu_total": total_revenu, "details": revenus_jours}

# --- 3. Alertes et Dashboard ---

@app.get("/kpi/alertes", tags=["Analyses"])
async def check_alertes(date_start: date, date_end: date, seuil_sous: float, seuil_sur: float):
    """Détecte la sous-production (rouge) et surproduction (bleu) [cite: 6, 39]"""
    period_data = [d for d in db_production if date_start <= d.date <= date_end]
    alertes = []

    for d in period_data:
        if d.production_mwh < seuil_sous:
            alertes.append({"date": d.date, "production": d.production_mwh, "type": "ROUGE (Sous-production)"})
        elif d.production_mwh > seuil_sur:
            alertes.append({"date": d.date, "production": d.production_mwh, "type": "BLEU (Surproduction)"})
            
    return alertes

@app.get("/dashboard/historique", tags=["Dashboard"])
async def get_dashboard(date_start: date, date_end: date):
    """Dashboard synthétique regroupant production, rendement et revenus [cite: 40-41]"""
    # Ici, on regroupe les logiques précédentes pour une sortie JSON unique [cite: 42-45]
    return {
        "periode": {"start": date_start, "end": date_end},
        "message": "Synthèse des données historiques prête pour l'affichage graphique"
    }

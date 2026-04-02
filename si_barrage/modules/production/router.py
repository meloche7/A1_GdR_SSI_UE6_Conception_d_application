# Endpoints de l'API pour la production
from datetime import date
from typing import List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from .models import MeteoHistoriqueModel, ProductionDataModel

router = APIRouter()


# --- DATA & CONSTANTS (from Calcul et simulation.py) ---
production_data = pd.DataFrame(
    {
        "date": [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-06",
            "2024-01-07",
            "2024-01-08",
            "2024-01-09",
            "2024-01-10",
        ],
        "production_mwh": [2500, 3200, 3800, 3500, 3000, 2800, 4200, 4800, 4500, 4100],
        "volume_eau_m3": [
            5000000,
            6400000,
            7600000,
            7000000,
            6000000,
            5600000,
            8400000,
            9600000,
            9000000,
            8200000,
        ],
    }
)

meteo_historique = pd.DataFrame(
    {
        "date": [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
            "2024-01-04",
            "2024-01-05",
            "2024-01-06",
            "2024-01-07",
            "2024-01-08",
            "2024-01-09",
            "2024-01-10",
        ],
        "debit_riviere_m3s": [
            120.5,
            135.2,
            150.0,
            142.8,
            130.1,
            125.7,
            160.3,
            185.0,
            170.4,
            158.6,
        ],
        "pluviometrie_mm": [5.2, 15.0, 8.5, 2.1, 0.0, 0.5, 25.8, 12.3, 4.0, 1.0],
    }
)

meteo_prevision = pd.DataFrame(
    {
        "date_prevision": ["2024-01-11", "2024-01-12", "2024-01-13", "2024-01-14"],
        "debit_riviere_m3s_prevu": [155.0, 150.0, 168.0, 180.0],
    }
)

production_data["date"] = pd.to_datetime(production_data["date"])
meteo_historique["date"] = pd.to_datetime(meteo_historique["date"])
df = production_data.merge(meteo_historique, on="date")

PRIX_ELECTRICITE = 120
NB_TURBINES = 4
PUISSANCE_NOMINALE = 50
df["efficacite"] = df["production_mwh"] / df["volume_eau_m3"]
EFFICACITE_MOYENNE = df["efficacite"].mean()
df["production_max"] = NB_TURBINES * PUISSANCE_NOMINALE * 24
df["taux_charge"] = (df["production_mwh"] / df["production_max"]) * 100
df["revenu"] = df["production_mwh"] * PRIX_ELECTRICITE

meteo_prevision["date_prevision"] = pd.to_datetime(meteo_prevision["date_prevision"])
meteo_prevision["volume_estime_m3"] = meteo_prevision["debit_riviere_m3s_prevu"] * 86400
meteo_prevision["production_estimee_mwh"] = (
    meteo_prevision["volume_estime_m3"] * EFFICACITE_MOYENNE
)
production_max = NB_TURBINES * PUISSANCE_NOMINALE * 24
meteo_prevision["production_estimee_mwh"] = meteo_prevision[
    "production_estimee_mwh"
].clip(upper=production_max)
meteo_prevision["revenu_estime"] = (
    meteo_prevision["production_estimee_mwh"] * PRIX_ELECTRICITE
)


# --- API Models and Endpoints (from alertes.py, Calcul et simulation.py) ---


db_production: List[ProductionDataModel] = []
db_meteo: List[MeteoHistoriqueModel] = []
config = {
    "prix_electricite": 120.0,
    "seuil_sous_prod": 3000.0,
    "seuil_sur_prod": 4500.0,
}


@router.get("/", response_class=HTMLResponse)
async def root():
    # Production chart
    fig_prod = go.Figure()
    fig_prod.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["production_mwh"],
            name="Production",
            line=dict(color="black"),
        )
    )
    fig_prod.update_layout(
        title="Production (MWh)", height=350, margin=dict(l=20, r=20, t=40, b=20)
    )
    prod_html = fig_prod.to_html(full_html=False, include_plotlyjs="cdn")

    # Rendement chart
    fig_rend = px.line(
        df, x="date", y="efficacite", title="Efficacité Hydraulique (MWh/m³)"
    )
    fig_rend.update_layout(height=350)
    rend_html = fig_rend.to_html(full_html=False, include_plotlyjs=False)

    # Revenu chart
    fig_rev = px.line(df, x="date", y="revenu", title="Revenu Journalier (€)")
    fig_rev.update_layout(height=320)
    rev_html = fig_rev.to_html(full_html=False, include_plotlyjs=False)

    # Taux de charge chart
    fig_taux = px.line(df, x="date", y="taux_charge", title="Taux de charge (%)")
    fig_taux.update_layout(height=320)
    taux_html = fig_taux.to_html(full_html=False, include_plotlyjs=False)

    # Simulation chart (prévision)
    fig_sim = go.Figure()
    fig_sim.add_trace(
        go.Bar(
            x=meteo_prevision["date_prevision"],
            y=meteo_prevision["production_estimee_mwh"],
            name="Production estimée (MWh)",
            marker_color="#2ca02c",
        )
    )
    fig_sim.add_trace(
        go.Bar(
            x=meteo_prevision["date_prevision"],
            y=meteo_prevision["revenu_estime"],
            name="Revenu estimé (€)",
            marker_color="#1f77b4",
        )
    )
    fig_sim.update_layout(
        barmode="group",
        title="Simulation de production et revenu",
        height=320,
        xaxis_title="Date prévision",
        yaxis_title="Valeur",
    )
    sim_html = fig_sim.to_html(full_html=False, include_plotlyjs=False)

    # Alertes chart (points sous/sur production)
    seuil_bas = config["seuil_sous_prod"]
    seuil_haut = config["seuil_sur_prod"]
    alert_low = df[df["production_mwh"] < seuil_bas]
    alert_high = df[df["production_mwh"] > seuil_haut]
    fig_alert = go.Figure()
    fig_alert.add_trace(
        go.Scatter(
            x=df["date"],
            y=df["production_mwh"],
            name="Production",
            line=dict(color="black"),
        )
    )
    fig_alert.add_trace(
        go.Scatter(
            x=alert_low["date"],
            y=alert_low["production_mwh"],
            mode="markers",
            name="Sous-prod",
            marker=dict(color="red", size=10),
        )
    )
    fig_alert.add_trace(
        go.Scatter(
            x=alert_high["date"],
            y=alert_high["production_mwh"],
            mode="markers",
            name="Sur-prod",
            marker=dict(color="orange", size=10),
        )
    )
    fig_alert.add_hline(
        y=seuil_bas, line_dash="dash", line_color="red", annotation_text="Seuil Bas"
    )
    fig_alert.add_hline(
        y=seuil_haut, line_dash="dash", line_color="blue", annotation_text="Seuil Haut"
    )
    fig_alert.update_layout(
        title="Alertes Production", height=350, margin=dict(l=20, r=20, t=40, b=20)
    )
    alert_html = fig_alert.to_html(full_html=False, include_plotlyjs=False)
    alertes = []
    if not alert_low.empty:
        for i, row in alert_low.iterrows():
            alertes.append(
                f"{row['date'].date()} - Sous production {row['production_mwh']} MWh"
            )
    if not alert_high.empty:
        for i, row in alert_high.iterrows():
            alertes.append(
                f"{row['date'].date()} - Surproduction {row['production_mwh']} MWh"
            )
    alerte_banner = ""
    if alertes:
        alerte_items = "<br>".join(alertes)
        alerte_banner = f"""
		<div style='background:#ffe9e9;border:1px solid #ff7f7f;padding:10px;margin-bottom:14px;border-radius:6px;'>
			<strong style='color:#b30000;'>⚠️ ALERTES DE SEUIL</strong>
			<p style='margin:4px 0;'>{len(alertes)} dépassement(s) détecté(s) (seuil sous={seuil_bas}, seuil sur={seuil_haut}).</p>
			<p style='margin:0;line-height:1.4;'>{alerte_items}</p>
		</div>
		"""
    df_html = df.to_html(index=False, classes="table", border=1)
    meteo_prevision_html = meteo_prevision.to_html(
        index=False, classes="table", border=1
    )

    return f"""
	<html>
	<head>
		<title>Dashboard Production</title>
		<style>
			.table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; }}
			.table th, .table td {{ border: 1px solid #ccc; padding: 4px 6px; text-align: center; }}
			.table th {{ background:#f1f1f1; }}
		</style>
	</head>
	<body style='background:#f8f9fa;'>
		<div style='max-width:1100px;margin:30px auto;font-family:Arial,Helvetica,sans-serif;'>
			<h1 style='text-align:center'>Dashboard Production</h1>
			<p style='text-align:center; margin-bottom:24px;'>Voir tous les résultats merge : <a href='/merged-results'>/merged-results</a></p>
			{alerte_banner}
			<div>{prod_html}</div>
			<div>{rend_html}</div>
			<div>{rev_html}</div>
			<div>{taux_html}</div>
			<div>{sim_html}</div>
			<div>{alert_html}</div>
			<h2>Résultats du merge (production + météo historique)</h2>
			<div style='overflow:auto; max-height:380px; border: 1px solid #ddd; background: white; padding: 10px;'>{df_html}</div>
			<h2>Prévisions avec production estimée</h2>
			<div style='overflow:auto; max-height:260px; border: 1px solid #ddd; background: white; padding: 10px;'>{meteo_prevision_html}</div>
		</div>
	</body>
	</html>
	"""


@router.post("/production/saisie", tags=["Entrées"])
async def saisie_production_v2(data: ProductionDataModel):
    db_production.append(data)
    return {"status": "confirmation", "message": "Donnée enregistrée"}


@router.post("/meteo/import", tags=["Entrées"])
async def import_meteo(data: List[MeteoHistoriqueModel]):
    db_meteo.extend(data)
    return {"status": "confirmation", "nb_records": len(data)}


@router.post("/prix/production", tags=["Configuration"])
async def set_prix(prix: float):
    config["prix_electricite"] = prix
    return {"status": "confirmation"}


@router.get("/kpi/rendement", tags=["Analyses"])
async def get_rendement_v2(date_start: date, date_end: date):
    period_data = [d for d in db_production if date_start <= d.date <= date_end]
    if not period_data:
        return {"message": "Utilisez les endpoints POST pour alimenter la base API."}
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
        "rendement_moyen": total_prod / total_vol if total_vol > 0 else 0,
    }


@router.get("/kpi/revenu", tags=["Analyses"])
async def get_revenu(date_start: date, date_end: date):
    period_data = [d for d in db_production if date_start <= d.date <= date_end]
    revenus_jours = [
        {"date": d.date, "revenu": d.production_mwh * config["prix_electricite"]}
        for d in period_data
    ]
    total_revenu = sum(item["revenu"] for item in revenus_jours)
    return {"revenu_total": total_revenu, "details": revenus_jours}


@router.get("/kpi/alertes", tags=["Analyses"])
async def check_alertes(
    date_start: date, date_end: date, seuil_sous: float, seuil_sur: float
):
    period_data = [d for d in db_production if date_start <= d.date <= date_end]
    alertes = []
    for d in period_data:
        if d.production_mwh < seuil_sous:
            alertes.append(
                {
                    "date": d.date,
                    "production": d.production_mwh,
                    "type": "ROUGE (Sous-production)",
                }
            )
        elif d.production_mwh > seuil_sur:
            alertes.append(
                {
                    "date": d.date,
                    "production": d.production_mwh,
                    "type": "BLEU (Surproduction)",
                }
            )
    return alertes


@router.get("/dashboard/historique", tags=["Dashboard"])
async def get_dashboard(date_start: date, date_end: date):
    return {
        "periode": {"start": date_start, "end": date_end},
        "message": "Synthèse des données historiques prête pour l'affichage graphique",
    }


@router.get("/merged-results", response_class=HTMLResponse, tags=["Dashboard"])
async def merged_results():
    df_html = df.to_html(index=False, classes="table", border=1)
    meteo_prevision_html = meteo_prevision.to_html(
        index=False, classes="table", border=1
    )
    return f"""
	<html>
	<head>
		<title>Résultats Merge</title>
		<style>
			.table {{ border-collapse: collapse; width: 100%; margin-bottom: 18px; }}
			.table th, .table td {{ border: 1px solid #ccc; padding: 4px 6px; text-align: center; }}
			.table th {{ background:#f1f1f1; }}
		</style>
	</head>
	<body style='background:#f8f9fa;'>
		<div style='max-width:1100px;margin:30px auto;font-family:Arial,Helvetica,sans-serif;'>
			<h1>Résultats des fichiers merge</h1>
			<p>Voici toutes les lignes du DataFrame fusionné:</p>
			<h2>Merge production + météo historique</h2>
			<div style='overflow:auto; max-height:380px; border:1px solid #ddd; background:white; padding:8px;'>{df_html}</div>
			<h2>Prévision de production estimée</h2>
			<div style='overflow:auto; max-height:260px; border:1px solid #ddd; background:white; padding:8px;'>{meteo_prevision_html}</div>
			<p><a href='/'>Retour au dashboard</a></p>
		</div>
	</body>
	</html>
	"""

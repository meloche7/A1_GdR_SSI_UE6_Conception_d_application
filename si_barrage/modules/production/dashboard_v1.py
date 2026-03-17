
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider
from fastapi import FastAPI, Form, HTTPException, Query
from fastapi.responses import HTMLResponse
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, date
from typing import List, Optional, Dict
from pydantic import BaseModel

# --- DATA & CONSTANTS (from Calcul et simulation.py) ---
production_data = pd.DataFrame({
	"date": [
		"2024-01-01","2024-01-02","2024-01-03","2024-01-04","2024-01-05",
		"2024-01-06","2024-01-07","2024-01-08","2024-01-09","2024-01-10"
	],
	"production_mwh": [2500,3200,3800,3500,3000,2800,4200,4800,4500,4100],
	"volume_eau_m3": [5000000,6400000,7600000,7000000,6000000,5600000,8400000,9600000,9000000,8200000]
})

meteo_historique = pd.DataFrame({
	"date": [
		"2024-01-01","2024-01-02","2024-01-03","2024-01-04","2024-01-05",
		"2024-01-06","2024-01-07","2024-01-08","2024-01-09","2024-01-10"
	],
	"debit_riviere_m3s": [120.5,135.2,150.0,142.8,130.1,125.7,160.3,185.0,170.4,158.6],
	"pluviometrie_mm": [5.2,15.0,8.5,2.1,0.0,0.5,25.8,12.3,4.0,1.0]
})

meteo_prevision = pd.DataFrame({
	"date_prevision": ["2024-01-11","2024-01-12","2024-01-13","2024-01-14"],
	"debit_riviere_m3s_prevu": [155.0,150.0,168.0,180.0]
})

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
meteo_prevision["volume_estime_m3"] = (
	meteo_prevision["debit_riviere_m3s_prevu"] * 86400
)
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


app = FastAPI(title="Dashboard Énergie - Mission Équipe 3")

# Simple dashboard with only charts at root
@app.get("/", response_class=HTMLResponse)
async def root():
	# Production chart
	import plotly.graph_objects as go
	import plotly.express as px
	fig_prod = go.Figure()
	fig_prod.add_trace(go.Scatter(x=df["date"], y=df["production_mwh"], name="Production", line=dict(color='black')))
	fig_prod.update_layout(title="Production (MWh)", height=350, margin=dict(l=20, r=20, t=40, b=20))
	prod_html = fig_prod.to_html(full_html=False, include_plotlyjs='cdn')

	# Rendement chart
	fig_rend = px.line(df, x="date", y="efficacite", title="Efficacité Hydraulique (MWh/m³)")
	fig_rend.update_layout(height=350)
	rend_html = fig_rend.to_html(full_html=False, include_plotlyjs=False)

	# Revenu chart
	fig_rev = px.line(df, x="date", y="revenu", title="Revenu Journalier (€)")
	fig_rev.update_layout(height=350)
	rev_html = fig_rev.to_html(full_html=False, include_plotlyjs=False)

	# Alertes chart (points sous/sur production)
	seuil_bas = 3000
	seuil_haut = 4500
	alert_low = df[df["production_mwh"] < seuil_bas]
	alert_high = df[df["production_mwh"] > seuil_haut]
	fig_alert = go.Figure()
	fig_alert.add_trace(go.Scatter(x=df["date"], y=df["production_mwh"], name="Production", line=dict(color='black')))
	fig_alert.add_trace(go.Scatter(x=alert_low["date"], y=alert_low["production_mwh"], mode='markers', name="Sous-prod", marker=dict(color='red', size=10)))
	fig_alert.add_trace(go.Scatter(x=alert_high["date"], y=alert_high["production_mwh"], mode='markers', name="Sur-prod", marker=dict(color='blue', size=10)))
	fig_alert.add_hline(y=seuil_bas, line_dash="dash", line_color="red", annotation_text="Seuil Bas")
	fig_alert.add_hline(y=seuil_haut, line_dash="dash", line_color="blue", annotation_text="Seuil Haut")
	fig_alert.update_layout(title="Alertes Production", height=350, margin=dict(l=20, r=20, t=40, b=20))
	alert_html = fig_alert.to_html(full_html=False, include_plotlyjs=False)

	return f"""
	<html>
	<head><title>Dashboard Énergie</title></head>
	<body style='background:#f8f9fa;'>
		<div style='max-width:1100px;margin:30px auto;'>
			<div>{prod_html}</div>
			<div>{rend_html}</div>
			<div>{rev_html}</div>
			<div>{alert_html}</div>
		</div>
	</body>
	</html>
	"""

# --- API Models and Endpoints (from alertes.py, Calcul et simulation.py) ---
class ProductionDataModel(BaseModel):
	date: date
	production_mwh: float
	volume_eau_m3: float

class MeteoHistoriqueModel(BaseModel):
	date: date
	debit_riviere_m3s: float
	pluviometrie_mm: float

db_production: List[ProductionDataModel] = []
db_meteo: List[MeteoHistoriqueModel] = []
config = {
	"prix_electricite": 120.0,
	"seuil_sous_prod": 3000.0,
	"seuil_sur_prod": 4500.0
}

@app.post("/production/saisie", tags=["Entrées"])
async def saisie_production_v2(data: ProductionDataModel):
	db_production.append(data)
	return {"status": "confirmation", "message": "Donnée enregistrée"}

@app.post("/meteo/import", tags=["Entrées"])
async def import_meteo(data: List[MeteoHistoriqueModel]):
	db_meteo.extend(data)
	return {"status": "confirmation", "nb_records": len(data)}

@app.post("/prix/production", tags=["Configuration"])
async def set_prix(prix: float):
	config["prix_electricite"] = prix
	return {"status": "confirmation"}

@app.get("/kpi/rendement", tags=["Analyses"])
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
		"rendement_moyen": total_prod / total_vol if total_vol > 0 else 0
	}

@app.get("/kpi/revenu", tags=["Analyses"])
async def get_revenu(date_start: date, date_end: date):
	period_data = [d for d in db_production if date_start <= d.date <= date_end]
	revenus_jours = [
		{"date": d.date, "revenu": d.production_mwh * config["prix_electricite"]} 
		for d in period_data
	]
	total_revenu = sum(item["revenu"] for item in revenus_jours)
	return {"revenu_total": total_revenu, "details": revenus_jours}

@app.get("/kpi/alertes", tags=["Analyses"])
async def check_alertes(date_start: date, date_end: date, seuil_sous: float, seuil_sur: float):
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
	return {
		"periode": {"start": date_start, "end": date_end},
		"message": "Synthèse des données historiques prête pour l'affichage graphique"
	}

# --- Matplotlib DEMO functions from alertes.py & seuils.py & GRAPHIQUE.py ---
def demo_matplotlib_alertes():
	x = np.linspace(0, 4*np.pi, 500)
	y = np.sin(x)
	seuil_bas_init = -0.5
	seuil_haut_init = 0.5
	fig, ax = plt.subplots()
	plt.subplots_adjust(bottom=0.3)
	courbe, = ax.plot(x, y, 'b-', lw=2, label='Courbe')
	ax.axhline(seuil_bas_init, color='r', linestyle='--', alpha=0.7, label='Seuil bas')
	ax.axhline(seuil_haut_init, color='g', linestyle='--', alpha=0.7, label='Seuil haut')
	ax.set_xlabel('x')
	ax.set_ylabel('y')
	ax.set_title('Alerte visuelle quand la courbe dépasse les seuils')
	ax.legend()
	ax.grid(True)
	ax_seuil_bas = plt.axes([0.15, 0.15, 0.65, 0.03])
	ax_seuil_haut = plt.axes([0.15, 0.1, 0.65, 0.03])
	slider_bas = Slider(ax_seuil_bas, 'Seuil bas', -2, 2, valinit=seuil_bas_init, valstep=0.05)
	slider_haut = Slider(ax_seuil_haut, 'Seuil haut', -2, 2, valinit=seuil_haut_init, valstep=0.05)
	def mise_a_jour(val):
		bas = slider_bas.val
		haut = slider_haut.val
		if bas >= haut:
			haut = bas + 0.1
			slider_haut.set_val(haut)
		ax.clear()
		ax.plot(x, y, 'b-', lw=2)
		ax.axhline(bas, color='r', linestyle='--', alpha=0.7)
		ax.axhline(haut, color='g', linestyle='--', alpha=0.7)
		ax.set_xlabel('x')
		ax.set_ylabel('y')
		ax.set_title('Alerte visuelle quand la courbe dépasse les seuils')
		ax.grid(True)
		ax.legend(['Courbe', 'Seuil bas', 'Seuil haut'])
		depasse_bas = y < bas
		depasse_haut = y > haut
		if np.any(depasse_bas) or np.any(depasse_haut):
			x_depasse_bas = x[depasse_bas]
			y_depasse_bas = y[depasse_bas]
			x_depasse_haut = x[depasse_haut]
			y_depasse_haut = y[depasse_haut]
			ax.scatter(x_depasse_bas, y_depasse_bas, color='red', s=10, zorder=5)
			ax.scatter(x_depasse_haut, y_depasse_haut, color='red', s=10, zorder=5)
			alerte = "ALERTE : dépassement de seuil !"
		else:
			alerte = ""
		ax.text(0.5, 0.95, alerte, transform=ax.transAxes, ha='center', color='red', fontsize=12, weight='bold')
		fig.canvas.draw_idle()
	slider_bas.on_changed(mise_a_jour)
	slider_haut.on_changed(mise_a_jour)
	plt.show()

def demo_matplotlib_seuils():
	x = np.linspace(0, 10, 500)
	def calculer_courbe(seuil1, seuil2):
		y = np.piecewise(x,
						 [x < seuil1, (x >= seuil1) & (x <= seuil2), x > seuil2],
						 [0, lambda x: (x - seuil1) / (seuil2 - seuil1), 1])
		return y
	seuil1_init = 2.0
	seuil2_init = 7.0
	fig, ax = plt.subplots()
	plt.subplots_adjust(bottom=0.25)
	y_init = calculer_courbe(seuil1_init, seuil2_init)
	courbe, = ax.plot(x, y_init, lw=2)
	ax.set_xlabel('x')
	ax.set_ylabel('y')
	ax.set_title('Courbe modifiable avec seuils')
	ax.grid(True)
	ax_seuil1 = plt.axes([0.15, 0.1, 0.65, 0.03])
	ax_seuil2 = plt.axes([0.15, 0.05, 0.65, 0.03])
	slider_seuil1 = Slider(ax_seuil1, 'Seuil 1', 0, 10, valinit=seuil1_init, valstep=0.1)
	slider_seuil2 = Slider(ax_seuil2, 'Seuil 2', 0, 10, valinit=seuil2_init, valstep=0.1)
	def mise_a_jour(val):
		s1 = slider_seuil1.val
		s2 = slider_seuil2.val
		if s1 >= s2:
			s2 = s1 + 0.1
			slider_seuil2.set_val(s2)
		y_new = calculer_courbe(s1, s2)
		courbe.set_ydata(y_new)
		fig.canvas.draw_idle()
	slider_seuil1.on_changed(mise_a_jour)
	slider_seuil2.on_changed(mise_a_jour)
	plt.show()

if __name__ == "__main__":
	import uvicorn
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

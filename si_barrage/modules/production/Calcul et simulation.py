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
efficacite_moyenne = df["efficacite"].mean()

df["production_max"] = NB_TURBINES * PUISSANCE_NOMINALE * 24
df["taux_charge"] = (df["production_mwh"] / df["production_max"]) * 100
df["revenu"] = df["production_mwh"] * PRIX_ELECTRICITE

print("\n===== KPI STRATÉGIQUES =====")
print("Production totale :", df["production_mwh"].sum(), "MWh")
print("Efficacité moyenne :", round(efficacite_moyenne,6), "MWh/m³")
print("Taux de charge moyen :", round(df["taux_charge"].mean(),2), "%")
print("Revenu total :", df["revenu"].sum(), "€")
print("Corrélation débit/production :", round(df["production_mwh"].corr(df["debit_riviere_m3s"]),4))


meteo_prevision["date_prevision"] = pd.to_datetime(meteo_prevision["date_prevision"])

meteo_prevision["volume_estime_m3"] = (
    meteo_prevision["debit_riviere_m3s_prevu"] * 86400
)

meteo_prevision["production_estimee_mwh"] = (
    meteo_prevision["volume_estime_m3"] * efficacite_moyenne
)

production_max = NB_TURBINES * PUISSANCE_NOMINALE * 24

meteo_prevision["production_estimee_mwh"] = meteo_prevision[
    "production_estimee_mwh"
].clip(upper=production_max)

meteo_prevision["revenu_estime"] = (
    meteo_prevision["production_estimee_mwh"] * PRIX_ELECTRICITE
)

print("\n===== SIMULATION FUTURE =====")
print(meteo_prevision[["date_prevision",
                        "production_estimee_mwh",
                        "revenu_estime"]])



fig, axs = plt.subplots(2, 3, figsize=(18, 10))

ax1 = axs[0,0]
ax1.plot(df["date"], df["production_mwh"], color="black", marker="o")
ax1.set_title("Production vs Volume d'eau")
ax1.set_ylabel("Production (MWh)")
ax1.tick_params(axis='x', rotation=45)

ax2 = ax1.twinx()
ax2.plot(df["date"], df["volume_eau_m3"], color="black", linestyle="--")
ax2.set_ylabel("Volume (m³)")

# Histogramme Production (distribution réelle)
axs[0,1].hist(df["production_mwh"], bins=6, edgecolor="black", color="white")
axs[0,1].set_title("Distribution de la Production")
axs[0,1].set_xlabel("Production (MWh)")
axs[0,1].set_ylabel("Fréquence")

#  Efficacité hydraulique
axs[0,2].plot(df["date"], df["efficacite"], color="black", marker="o")
axs[0,2].set_title("Efficacité Hydraulique")
axs[0,2].tick_params(axis='x', rotation=45)

#  Revenu journalier
axs[1,0].plot(df["date"], df["revenu"], color="black", marker="o")
axs[1,0].set_title("Revenu Journalier")
axs[1,0].tick_params(axis='x', rotation=45)

# Relation Débit / Production (ligne reliant les points)
df_sorted = df.sort_values("debit_riviere_m3s")
axs[1,1].plot(df_sorted["debit_riviere_m3s"],
              df_sorted["production_mwh"],
              color="black",
              marker="o")
axs[1,1].set_title("Débit vs Production")
axs[1,1].set_xlabel("Débit (m³/s)")
axs[1,1].set_ylabel("Production (MWh)")

# Simulation future
axs[1,2].plot(meteo_prevision["date_prevision"],
              meteo_prevision["production_estimee_mwh"],
              color="black",
              marker="o")
axs[1,2].set_title("Production Estimée Future")
axs[1,2].tick_params(axis='x', rotation=45)

plt.suptitle("Dashboard Stratégique – Suivi et Simulation de Production", fontsize=16)
plt.tight_layout()
plt.show()

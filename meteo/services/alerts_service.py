def detect_alerts(data):

    alerts = []

    for row in data:

        if row.pluviometrie_mm_prevue > 40:
            alerts.append({
                "date": str(row.date_prevision),
                "type": "FORTES_PLUIES",
                "niveau": "ALERTE"
            })

        if row.debit_riviere_m3s_prevu > 170:
            alerts.append({
                "date": str(row.date_prevision),
                "type": "RISQUE_CRUE",
                "niveau": "CRITIQUE"
            })

    return alerts
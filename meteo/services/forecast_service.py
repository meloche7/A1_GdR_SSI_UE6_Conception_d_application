from sqlalchemy.orm import Session
from meteo.models.forecast import MeteoPrevision


def get_forecasts(db: Session):

    return db.query(MeteoPrevision)\
             .order_by(MeteoPrevision.date_prevision)\
             .all()


def compute_indicators(data):

    debit_values = [row.debit_riviere_m3s_prevu for row in data]
    pluie_values = [row.pluviometrie_mm_prevue for row in data]

    return {
        "pluie_totale_7j": sum(pluie_values[:7]),
        "debit_max": max(debit_values),
        "debit_moyen": sum(debit_values) / len(debit_values)
    }
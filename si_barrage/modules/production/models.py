from datetime import date

from pydantic import BaseModel


class ProductionDataModel(BaseModel):
    date: date
    production_mwh: float
    volume_eau_m3: float


class MeteoHistoriqueModel(BaseModel):
    date: date
    debit_riviere_m3s: float
    pluviometrie_mm: float

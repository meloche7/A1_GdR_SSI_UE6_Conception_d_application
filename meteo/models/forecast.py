from sqlalchemy import Column, Integer, Float, Date
from meteo.database import Base


class MeteoPrevision(Base):
    __tablename__ = "meteo_previsions"

    id = Column(Integer, primary_key=True, index=True)
    date_prevision = Column(Date)
    date_creation = Column(Date)
    debit_riviere_m3s_prevu = Column(Float)
    pluviometrie_mm_prevue = Column(Float)
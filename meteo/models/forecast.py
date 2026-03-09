"""
Modèles SQLAlchemy pour les prévisions, alertes et données existantes
Adapté à la structure existante de barrage.db
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from ..database import Base

# ============= MODÈLES SQLALCHEMY EXISTANTS (BD) =============

class MeteoActuelleDB(Base):
    """Modèle BD pour les données météo actuelles"""
    __tablename__ = "meteo"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    debit_riviere_m3s = Column(Float)
    pluviometrie_mm = Column(Float)

class ProductionDB(Base):
    """Modèle BD pour la production électrique"""
    __tablename__ = "production"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, index=True)
    production_mwh = Column(Float)
    volume_eau_m3 = Column(Integer)

class MaintenanceDB(Base):
    """Modèle BD pour la maintenance des équipements"""
    __tablename__ = "maintenance"
    
    id = Column(Integer, primary_key=True, index=True)
    id_equipement = Column(String)
    nom_equipement = Column(String)
    statut = Column(String)
    description = Column(String)
    date_creation = Column(String)

class MeteoPrevisionsDB(Base):
    """Modèle BD pour les prévisions météo"""
    __tablename__ = "meteo_previsions"
    
    id = Column(Integer, primary_key=True, index=True)
    date_prevision = Column(String, index=True)
    date_creation = Column(String)
    debit_riviere_m3s_prevu = Column(Float)
    pluviometrie_mm_prevue = Column(Float)

# ============= MODÈLES SQLALCHEMY NOUVEAUX (À CRÉER) =============

class AlerteSystemeDB(Base):
    """Modèle BD pour les alertes"""
    __tablename__ = "alertes_systeme"
    
    id = Column(Integer, primary_key=True, index=True)
    type_alerte = Column(String)
    niveau_severite = Column(String)
    message = Column(String)
    date_creation = Column(String)
    date_prévue = Column(String)
    recommandations = Column(String)  # Séparées par |
    traitée = Column(Integer, default=0)

class ParametreAlerteDB(Base):
    """Modèle BD pour les paramètres d'alerte"""
    __tablename__ = "parametres_alerte"
    
    clé = Column(String, primary_key=True, index=True)
    valeur = Column(String)
    description = Column(String)

# ============= MODÈLES PYDANTIC (API) =============

class MeteoActuelle(BaseModel):
    """Modèle API pour les données météo actuelles"""
    id: int = None
    date: str
    debit_riviere_m3s: float
    pluviometrie_mm: float
    
    class Config:
        from_attributes = True

class Production(BaseModel):
    """Modèle API pour la production"""
    id: int = None
    date: str
    production_mwh: float
    volume_eau_m3: int
    
    class Config:
        from_attributes = True

class Maintenance(BaseModel):
    """Modèle API pour la maintenance"""
    id: int = None
    id_equipement: str
    nom_equipement: str
    statut: str
    description: str
    date_creation: str
    
    class Config:
        from_attributes = True

class PrevisionMeteo(BaseModel):
    """Modèle API pour une prévision"""
    date_prevision: str
    date_creation: str
    debit_riviere_m3s_prevu: float
    pluviometrie_mm_prevue: float
    
    class Config:
        from_attributes = True

class AlerteSysteme(BaseModel):
    """Modèle API pour une alerte"""
    id: int = None
    type_alerte: str
    niveau_severite: str
    message: str
    date_creation: str
    date_prévue: str
    recommandations: list = []
    
    class Config:
        from_attributes = True

class ParametreAlerte(BaseModel):
    """Modèle API pour un paramètre"""
    clé: str
    valeur: float
    description: str = None
    
    class Config:
        from_attributes = True

class ResumePrevisions(BaseModel):
    """Résumé statistique des prévisions"""
    pluviometrie_moyenne: float
    pluviometrie_max: float
    debit_moyen: float
    debit_max: float
    alerte_majeure: AlerteSysteme = None

class ResumeDonnees(BaseModel):
    """Résumé global des données"""
    meteo_actuelle: MeteoActuelle = None
    derniere_production: Production = None
    maintenance_active: list[Maintenance] = []
    alertes_non_traitees: int = 0

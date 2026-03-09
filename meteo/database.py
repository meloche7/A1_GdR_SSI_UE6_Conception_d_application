"""
Configuration de la base de données SQLAlchemy
Utilise la BD existante barrage.db
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Configuration BD - Pointe vers barrage.db à la racine du projet
DATABASE_URL = "sqlite:///./barrage.db"

# Créer engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base pour les modèles
Base = declarative_base()

def get_db():
    """Dépendance pour obtenir la session BD"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialise les tables manquantes (alertes, paramètres)"""
    Base.metadata.create_all(bind=engine)

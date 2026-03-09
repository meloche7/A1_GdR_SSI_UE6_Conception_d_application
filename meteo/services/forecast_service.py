"""
Service pour gérer les prévisions météo
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.forecast import (
    MeteoPrevisionsDB,
    PrevisionMeteo,
    ResumePrevisions,
    AlerteSystemeDB,
    AlerteSysteme
)

class ForecastService:
    """Service pour les prévisions"""
    
    @staticmethod
    def get_previsions(db: Session, jours: int = 10) -> list[PrevisionMeteo]:
        """Récupère les prévisions"""
        date_debut = datetime.now().date().isoformat()
        date_fin = (datetime.now() + timedelta(days=jours)).date().isoformat()
        
        previsions = db.query(MeteoPrevisionsDB).filter(
            MeteoPrevisionsDB.date_prevision >= date_debut,
            MeteoPrevisionsDB.date_prevision <= date_fin
        ).order_by(MeteoPrevisionsDB.date_prevision).all()
        
        return [PrevisionMeteo.from_orm(p) for p in previsions]
    
    @staticmethod
    def get_resume(db: Session, jours: int = 10) -> ResumePrevisions:
        """Récupère le résumé des prévisions"""
        date_debut = datetime.now().date().isoformat()
        date_fin = (datetime.now() + timedelta(days=jours)).date().isoformat()
        
        previsions = db.query(MeteoPrevisionsDB).filter(
            MeteoPrevisionsDB.date_prevision >= date_debut,
            MeteoPrevisionsDB.date_prevision <= date_fin
        ).all()
        
        if not previsions:
            return ResumePrevisions(
                pluviometrie_moyenne=0,
                pluviometrie_max=0,
                debit_moyen=0,
                debit_max=0
            )
        
        debits = [p.debit_riviere_m3s_prevu for p in previsions]
        pluvios = [p.pluviometrie_mm_prevue for p in previsions]
        
        # Récupérer l'alerte majeure
        alerte = db.query(AlerteSystemeDB).filter(
            AlerteSystemeDB.traitée == 0
        ).order_by(AlerteSystemeDB.date_creation.desc()).first()
        
        alerte_obj = None
        if alerte:
            alerte_obj = AlerteSysteme(
                id=alerte.id,
                type_alerte=alerte.type_alerte,
                niveau_severite=alerte.niveau_severite,
                message=alerte.message,
                date_creation=alerte.date_creation,
                date_prévue=alerte.date_prévue,
                recommandations=alerte.recommandations.split("|") if alerte.recommandations else []
            )
        
        return ResumePrevisions(
            pluviometrie_moyenne=sum(pluvios) / len(pluvios) if pluvios else 0,
            pluviometrie_max=max(pluvios) if pluvios else 0,
            debit_moyen=sum(debits) / len(debits) if debits else 0,
            debit_max=max(debits) if debits else 0,
            alerte_majeure=alerte_obj
        )
    
    @staticmethod
    def importer_previsions(db: Session, previsions: list[PrevisionMeteo]) -> int:
        """Importe des prévisions"""
        for prev in previsions:
            new_prev = MeteoPrevisionsDB(
                date_prevision=prev.date_prevision,
                date_creation=prev.date_creation,
                debit_riviere_m3s_prevu=prev.debit_riviere_m3s_prevu,
                pluviometrie_mm_prevue=prev.pluviometrie_mm_prevue
            )
            db.add(new_prev)
        
        db.commit()
        return len(previsions)

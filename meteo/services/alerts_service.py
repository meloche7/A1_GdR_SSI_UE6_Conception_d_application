"""
Service pour gérer les alertes
"""

from sqlalchemy.orm import Session
from datetime import datetime
from ..models.forecast import AlerteSystemeDB, AlerteSysteme, ParametreAlerteDB

class AlertsService:
    """Service pour les alertes"""
    
    @staticmethod
    def get_alertes(db: Session, non_traitees_seulement: bool = False) -> list[AlerteSysteme]:
        """Récupère les alertes"""
        query = db.query(AlerteSystemeDB)
        
        if non_traitees_seulement:
            query = query.filter(AlerteSystemeDB.traitée == 0)
        
        alertes = query.order_by(AlerteSystemeDB.date_creation.desc()).limit(50).all()
        
        result = []
        for a in alertes:
            result.append(AlerteSysteme(
                id=a.id,
                type_alerte=a.type_alerte,
                niveau_severite=a.niveau_severite,
                message=a.message,
                date_creation=a.date_creation,
                date_prévue=a.date_prévue,
                recommandations=a.recommandations.split("|") if a.recommandations else []
            ))
        
        return result
    
    @staticmethod
    def creer_alerte(db: Session, alerte: AlerteSysteme) -> int:
        """Crée une nouvelle alerte"""
        rec_str = "|".join(alerte.recommandations) if alerte.recommandations else ""
        
        new_alerte = AlerteSystemeDB(
            type_alerte=alerte.type_alerte,
            niveau_severite=alerte.niveau_severite,
            message=alerte.message,
            date_creation=alerte.date_creation,
            date_prévue=alerte.date_prévue,
            recommandations=rec_str
        )
        
        db.add(new_alerte)
        db.commit()
        db.refresh(new_alerte)
        
        return new_alerte.id
    
    @staticmethod
    def marquer_alerte_traitee(db: Session, alerte_id: int) -> bool:
        """Marque une alerte comme traitée"""
        alerte = db.query(AlerteSystemeDB).filter(AlerteSystemeDB.id == alerte_id).first()
        if not alerte:
            return False
        
        alerte.traitée = 1
        db.commit()
        return True
    
    @staticmethod
    def detecter_alertes_automatiques(db: Session, previsions: list) -> list[int]:
        """
        Détecte automatiquement les situations critiques
        Retourne la liste des IDs des alertes créées
        """
        # Récupérer les paramètres
        params = AlertsService.get_parametres(db)
        
        seuil_debit_critique = params.get("DEBIT_CRITIQUE_M3S", 500)
        seuil_pluvio_critique = params.get("PLUVIO_CRITIQUE_MM", 100)
        seuil_pluvio_alerte = params.get("PLUVIO_ALERTE_MM", 50)
        seuil_debit_faible = params.get("DEBIT_FAIBLE_M3S", 50)
        
        alertes_creees = []
        
        for prev in previsions:
            debit = prev.debit_riviere_m3s_prevu
            pluvio = prev.pluviometrie_mm_prevue
            date_prev = prev.date_prevision
            
            # Pluie critique
            if pluvio >= seuil_pluvio_critique:
                alerte = AlerteSysteme(
                    type_alerte="ALERTE_PLUIE_CRITIQUE",
                    niveau_severite="CRITIQUE",
                    message=f"Forte pluviométrie prévue: {pluvio:.1f}mm",
                    date_creation=datetime.now().isoformat(),
                    date_prévue=date_prev,
                    recommandations=[
                        "Vérifier la capacité de retenue",
                        "Préparer les vannes de vidange",
                        "Notifier les autorités de sécurité civile"
                    ]
                )
                alertes_creees.append(AlertsService.creer_alerte(db, alerte))
            
            # Pluie élevée
            elif pluvio >= seuil_pluvio_alerte:
                alerte = AlerteSysteme(
                    type_alerte="ALERTE_PLUVIOSITÉ",
                    niveau_severite="ÉLEVÉE",
                    message=f"Pluviométrie élevée prévue: {pluvio:.1f}mm",
                    date_creation=datetime.now().isoformat(),
                    date_prévue=date_prev,
                    recommandations=[
                        "Surveiller le niveau de retenue",
                        "Préparer la gestion des débits"
                    ]
                )
                alertes_creees.append(AlertsService.creer_alerte(db, alerte))
            
            # Débit critique
            if debit >= seuil_debit_critique:
                alerte = AlerteSysteme(
                    type_alerte="ALERTE_DÉBIT",
                    niveau_severite="CRITIQUE",
                    message=f"Débit critique prévu: {debit:.1f}m³/s",
                    date_creation=datetime.now().isoformat(),
                    date_prévue=date_prev,
                    recommandations=[
                        "Réduire les débits sortants",
                        "Alerter les populations en aval"
                    ]
                )
                alertes_creees.append(AlertsService.creer_alerte(db, alerte))
            
            # Sécheresse
            elif debit <= seuil_debit_faible:
                alerte = AlerteSysteme(
                    type_alerte="SÉCHERESSE",
                    niveau_severite="MODÉRÉE",
                    message=f"Débit faible prévu (sécheresse): {debit:.1f}m³/s",
                    date_creation=datetime.now().isoformat(),
                    date_prévue=date_prev,
                    recommandations=[
                        "Réduire les prélèvements agricoles",
                        "Activer les mesures de restriction"
                    ]
                )
                alertes_creees.append(AlertsService.creer_alerte(db, alerte))
        
        return alertes_creees
    
    @staticmethod
    def get_parametres(db: Session) -> dict:
        """Récupère les paramètres d'alerte"""
        params = db.query(ParametreAlerteDB).all()
        
        result = {}
        for p in params:
            result[p.clé] = float(p.valeur)
        
        return result
    
    @staticmethod
    def update_parametre(db: Session, cle: str, valeur: float) -> bool:
        """Met à jour un paramètre"""
        param = db.query(ParametreAlerteDB).filter(ParametreAlerteDB.clé == cle).first()
        if not param:
            return False
        
        param.valeur = str(valeur)
        db.commit()
        return True
    
    @staticmethod
    def init_default_params(db: Session):
        """Initialise les paramètres par défaut"""
        defaults = [
            ("DEBIT_CRITIQUE_M3S", "500", "Débit critique (m³/s)"),
            ("PLUVIO_ALERTE_MM", "50", "Pluviométrie d'alerte (mm)"),
            ("PLUVIO_CRITIQUE_MM", "100", "Pluviométrie critique (mm)"),
            ("DEBIT_FAIBLE_M3S", "50", "Débit faible/sécheresse (m³/s)"),
        ]
        
        for cle, val, desc in defaults:
            existing = db.query(ParametreAlerteDB).filter(ParametreAlerteDB.clé == cle).first()
            if not existing:
                db.add(ParametreAlerteDB(clé=cle, valeur=val, description=desc))
        
        db.commit()

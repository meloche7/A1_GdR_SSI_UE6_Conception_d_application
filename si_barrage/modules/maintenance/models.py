from sqlalchemy import Column, Float, Integer, String

from si_barrage.db import Base


class MaintenanceTicket(Base):
    """
    Modèle unique de la table `maintenance`.

    Cette table centralise :
    - les tickets de maintenance
    - les interventions (historique)
    - les données du tableau de bord (TDB)

    Principe clé :
       UNE LIGNE = UN ÉVÉNEMENT (ticket ou intervention)
       donc plusieurs lignes possibles pour un même équipement
    """

    __tablename__ = "maintenance"

    # Clé primaire
    id = Column(Integer, primary_key=True, index=True)

    # ----------------------------
    # Identification équipement
    # ----------------------------
    id_equipement = Column(String, nullable=False, index=True)
    nom_equipement = Column(String, nullable=True)

    # ----------------------------
    # Ticket / suivi
    # ----------------------------
    statut = Column(String, nullable=True)  # En cours, Terminé, En attente, Supprimé
    description = Column(String, nullable=True)  # problème uniquement
    date_creation = Column(String, nullable=True)  # ISO: YYYY-MM-DD

    # ----------------------------
    # Intervention / historique
    # ----------------------------
    ticket_id = Column(Integer, nullable=True, index=True)
    date_intervention = Column(String, nullable=True, index=True)  # ISO: YYYY-MM-DD

    intervenant = Column(String, nullable=True)  # technicien
    solution = Column(String, nullable=True)

    # ----------------------------
    # Données complémentaires
    # ----------------------------
    duree_minutes = Column(Integer, nullable=True)
    cout = Column(Float, nullable=True)
    pieces_changees = Column(String, nullable=True)
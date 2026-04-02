from sqlalchemy import text


def get_equipment_events(db, prefix: str = "", status: str = ""):
    """
    Retourne les équipements à afficher dans le tableau de bord (TDB).

    Logique métier :
    - un même équipement peut avoir plusieurs lignes dans `maintenance`
    - on ne garde que la ligne la plus récente de chaque équipement
    - on exclut les lignes marquées 'Supprimé'
    - on applique les filtres éventuels
    - on limite l'affichage aux 5 dernières entrées visibles dans le TDB
    """

    params = {
        "prefix": prefix.upper() if prefix else "",
        "status": status if status else "",
    }

    result = db.execute(
        text("""
            WITH ranked AS (
                SELECT
                    id,
                    id_equipement,
                    COALESCE(nom_equipement, id_equipement) AS nom_equipement,
                    statut,
                    date_creation,
                    ticket_id,
                    description,

                    -- On numérote les lignes de chaque équipement
                    -- de la plus récente à la plus ancienne.
                    ROW_NUMBER() OVER (
                        PARTITION BY id_equipement
                        ORDER BY date_creation DESC, id DESC
                    ) AS rn
                FROM maintenance
                WHERE id_equipement IS NOT NULL
                  AND LENGTH(id_equipement) > 0
                  AND statut != 'Supprimé'
            )
            SELECT
                id,
                id_equipement,
                nom_equipement,
                statut,
                date_creation,
                ticket_id,
                description
            FROM ranked
            WHERE rn = 1
              AND (:prefix = '' OR UPPER(SUBSTR(id_equipement, 1, 1)) = :prefix)
              AND (:status = '' OR statut = :status)
            ORDER BY date_creation DESC, id DESC
            LIMIT 5
        """),
        params,
    ).fetchall()

    return [
        {
            "id": r[0],  # vrai identifiant de la ligne dans maintenance
            "id_equipement": r[1],
            "nom_equipement": r[2],
            "statut": r[3],
            "date_creation": r[4],
            "ticket_id": r[5],
            "description": r[6],
        }
        for r in result
    ]


def get_kpis(db):
    """
    Calcule les KPI du tableau de bord.

    Important :
    - on ne compte pas toutes les lignes historiques
    - on compte seulement le dernier état connu de chaque équipement
    - les lignes 'Supprimé' sont exclues
    """

    result = db.execute(
        text("""
            WITH ranked AS (
                SELECT
                    id,
                    id_equipement,
                    statut,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_equipement
                        ORDER BY date_creation DESC, id DESC
                    ) AS rn
                FROM maintenance
                WHERE id_equipement IS NOT NULL
                  AND LENGTH(id_equipement) > 0
                  AND statut != 'Supprimé'
            )
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN statut = 'Terminé' THEN 1 ELSE 0 END) AS termines,
                SUM(CASE WHEN statut = 'En cours' THEN 1 ELSE 0 END) AS encours,
                SUM(CASE WHEN statut = 'En attente' THEN 1 ELSE 0 END) AS attente
            FROM ranked
            WHERE rn = 1
        """)
    ).fetchone()

    return {
        "termines": result[1] or 0,
        "encours": result[2] or 0,
        "attente": result[3] or 0,
    }


def get_id_prefixes(db):
    """
    Retourne les préfixes disponibles pour le filtre du TDB.

    Exemple :

    On se base sur le dernier état connu de chaque équipement,
    pour que le filtre reste cohérent avec le tableau affiché.
    """

    rows = db.execute(
        text("""
            WITH ranked AS (
                SELECT
                    id,
                    id_equipement,
                    statut,
                    ROW_NUMBER() OVER (
                        PARTITION BY id_equipement
                        ORDER BY date_creation DESC, id DESC
                    ) AS rn
                FROM maintenance
                WHERE id_equipement IS NOT NULL
                  AND LENGTH(id_equipement) > 0
                  AND statut != 'Supprimé'
            )
            SELECT DISTINCT UPPER(SUBSTR(id_equipement, 1, 1)) AS prefix
            FROM ranked
            WHERE rn = 1
            ORDER BY prefix
        """)
    ).fetchall()

    return [r[0] for r in rows if r[0]]
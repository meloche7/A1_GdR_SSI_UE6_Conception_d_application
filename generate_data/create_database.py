import csv
import os
import sqlite3

DB_FILE = "barrage.db"
DATA_DIR = "generate_data"


def create_database():
    """
    Crée la base SQLite et toutes les tables nécessaires.

    Important :
    - si une ancienne base existe, elle est supprimée
    - on repart donc d'une base propre
    """
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    print("Creating tables...")

    # -------------------------------------------------
    # Table METEO
    # -------------------------------------------------
    cursor.execute("""
    CREATE TABLE meteo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        debit_riviere_m3s REAL,
        pluviometrie_mm REAL
    );
    """)

    # -------------------------------------------------
    # Table MAINTENANCE
    # -------------------------------------------------
    # Table centrale du projet.
    #
    # Elle regroupe :
    # - les tickets créés depuis l'interface
    # - les historiques d'interventions
    # - les informations nécessaires au TDB
    #
    # Rôle des champs principaux :
    # - id : identifiant réel de la ligne
    # - ticket_id : numéro fonctionnel du ticket
    #   (pour les nouveaux tickets, on pourra ensuite lui affecter id)
    # - description : problème
    # - intervenant : technicien
    # - solution : solution proposée / appliquée
    cursor.execute("""
    CREATE TABLE maintenance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        -- Identification équipement
        id_equipement TEXT NOT NULL,
        nom_equipement TEXT,

        -- Informations ticket / état
        statut TEXT,
        description TEXT,
        date_creation TEXT,

        -- Informations intervention / historique
        ticket_id INTEGER,
        date_intervention TEXT,
        intervenant TEXT,
        solution TEXT,

        -- Champs complémentaires
        duree_minutes INTEGER,
        cout REAL,
        pieces_changees TEXT
    );
    """)

    # -------------------------------------------------
    # Table PRODUCTION
    # -------------------------------------------------
    cursor.execute("""
    CREATE TABLE production (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date TEXT NOT NULL,
        production_mwh REAL,
        volume_eau_m3 INTEGER
    );
    """)

    # -------------------------------------------------
    # Table METEO_PREVISIONS
    # -------------------------------------------------
    cursor.execute("""
    CREATE TABLE meteo_previsions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_prevision TEXT NOT NULL,
        date_creation TEXT NOT NULL,
        debit_riviere_m3s_prevu REAL,
        pluviometrie_mm_prevue REAL
    );
    """)

    # --- Create intervention table ---
    cursor.execute("""
    CREATE TABLE intervention (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_equipement TEXT NOT NULL,
        date_intervention TEXT NOT NULL,
        intervenant TEXT,
        probleme TEXT,
        solution TEXT
    );
    """)

    # --- Create centrale_parametres table ---
    cursor.execute("""
    CREATE TABLE centrale_parametres (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_turbines INTEGER NOT NULL CHECK (nombre_turbines >= 0),
        puissance_nominale_mw REAL NOT NULL CHECK (puissance_nominale_mw >= 0),
        prix_electricite_eur_mwh REAL NOT NULL CHECK (prix_electricite_eur_mwh >= 0)
    );
    """)

    conn.commit()
    conn.close()
    print("Database and tables created successfully.")


def populate_table(table_name, csv_file):
    """
    Remplit une table à partir d’un fichier CSV.

    Comportement :
    - ignore les lignes vides
    - ignore les lignes mal formées
    - continue l'import même si une ligne pose problème
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    csv_path = os.path.join(DATA_DIR, csv_file)

    print(f"Populating table '{table_name}' from '{csv_path}'...")

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)  # Skip header row

        # Prepare the insert statement
        # The number of placeholders must match the number of columns in the CSV
        placeholders = ", ".join(["?"] * len(header))
        query = (
            f"INSERT INTO {table_name} ({', '.join(header)}) VALUES ({placeholders})"
        )

        # Read data and insert into the table
        count = 0

        for row in reader:
            # Ignore les lignes complètement vides
            if not row or all(not cell.strip() for cell in row):
                continue

            # Ignore les lignes mal formées
            if len(row) != len(header):
                print(
                    f"Skipping malformed row in '{csv_file}': "
                    f"expected {len(header)} values, got {len(row)} -> {row}"
                )
                continue

            try:
                cursor.execute(query, row)
                count += 1
            except Exception as e:
                print(f"Error inserting row into '{table_name}': {row}")
                print(e)

    conn.commit()
    conn.close()
    print(f"Inserted {count} rows into '{table_name}'.")


if __name__ == "__main__":
    create_database()

    populate_table("meteo", "meteo_data.csv")
    populate_table("maintenance", "maintenance_data.csv")
    populate_table("production", "production_data.csv")
    populate_table("meteo_previsions", "meteo_previsions_data.csv")
    print("\nDatabase generation complete.")
    print(f"Database file: '{DB_FILE}'")

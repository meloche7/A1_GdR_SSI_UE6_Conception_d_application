

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from si_barrage.main import app
from si_barrage.db import Base, get_db
from si_barrage.modules.maintenance.models import MaintenanceTicket, Intervention

client = TestClient(app)


def make_test_db():
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)

    # Seed minimal data
    db = TestingSessionLocal()
    t1 = MaintenanceTicket(id_equipement="T1", nom_equipement="Turbine 1", statut="Terminé",
                          description="Vibration anormale", date_creation="2024-01-02")
    v3 = MaintenanceTicket(id_equipement="V3", nom_equipement="Vanne 3", statut="En cours",
                          description="La vanne ne se ferme pas", date_creation="2024-01-05")
    db.add_all([t1, v3])
    db.commit()
    db.refresh(t1)
    db.refresh(v3)

    i1 = Intervention(
        id_equipement="T1",
        ticket_id=t1.id,
        date_intervention="2024-02-10",
        intervenant="Amina",
        probleme="Vibration anormale",
        solution="Roulements changés",
        statut="Terminé",
    )
    i2 = Intervention(
        id_equipement="T1",
        ticket_id=t1.id,
        date_intervention="2024-03-15",
        intervenant="Jean",
        probleme="Surchauffe",
        solution="Nettoyage circuit huile",
        statut="Terminé",
    )
    i3 = Intervention(
        id_equipement="V3",
        ticket_id=v3.id,
        date_intervention="2024-01-06",
        intervenant="Paul",
        probleme="Vanne ne se ferme pas",
        solution="Réglage actionneur",
        statut="En cours",
    )
    db.add_all([i1, i2, i3])
    db.commit()
    db.refresh(i1)
    db.refresh(i2)
    db.refresh(i3)
    db.close()

    return engine, TestingSessionLocal, {"i1": i1.id, "i2": i2.id, "i3": i3.id}


def override_get_db(TestingSessionLocal):
    def _override():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()
    return _override


def setup_module(module):
    engine, TestingSessionLocal, ids = make_test_db()
    module._ids = ids
    app.dependency_overrides[get_db] = override_get_db(TestingSessionLocal)


def teardown_module(module):
    app.dependency_overrides.clear()


def test_get_interventions_list():
    response = client.get("/maintenance/equipements/T1/interventions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # tri date desc => 2024-03-15 en premier
    assert data[0]["date_intervention"] == "2024-03-15"
    assert data[1]["date_intervention"] == "2024-02-10"


def test_get_intervention_detail():
    intervention_id = _ids["i1"]
    response = client.get(f"/maintenance/interventions/{intervention_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == intervention_id
    assert data["id_equipement"] == "T1"
    assert data["probleme"] == "Vibration anormale"


def test_analyse_interventions():
    response = client.get("/maintenance/equipements/T1/interventions/analyse?top_n=5")
    assert response.status_code == 200
    data = response.json()
    assert data["id_equipement"] == "T1"
    assert data["total_interventions"] == 2
    problemes = [p["probleme"] for p in data["top_problemes"]]
    assert "Vibration anormale" in problemes
    assert "Surchauffe" in problemes


def test_errors_404_equipment_unknown():
    resp = client.get("/maintenance/equipements/XXX/interventions")
    assert resp.status_code == 404


def test_errors_404_intervention_unknown():
    resp = client.get("/maintenance/interventions/999999")
    assert resp.status_code == 404
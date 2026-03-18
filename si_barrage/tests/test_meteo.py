from fastapi.testclient import TestClient
from si_barrage.main import app

client = TestClient(app)

def test_get_releves():
    """Test the /meteo/releves endpoint."""
    response = client.get("/meteo/releves")
    assert response.status_code == 200
    # Should return a list of relevés (possibly empty if la base de données est vide).
    assert isinstance(response.json(), list)


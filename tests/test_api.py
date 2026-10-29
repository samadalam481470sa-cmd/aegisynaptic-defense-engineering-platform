from fastapi.testclient import TestClient
from aegisynaptic.api import app

client = TestClient(app)

def test_health():
    assert client.get("/api/health").json()["mode"] == "synthetic"

def test_dashboard():
    response = client.get("/")
    assert response.status_code == 200
    assert "AEGISYNAPTIC" in response.text

def test_unknown_asset():
    assert client.get("/api/assets/DOES-NOT-EXIST/telemetry").status_code == 404

def test_analysis():
    response = client.get("/api/fleet/analysis")
    assert response.status_code == 200
    assert response.json()["synthetic"] is True

def test_request_validation():
    assert client.post("/api/maintenance/optimize", json={"budget": -1}).status_code == 422

def test_simulation():
    response = client.post("/api/assets/GEN-101/simulate",
                           json={"trials": 20, "horizon_hours": 64})
    assert response.status_code == 200
    assert response.json()["trials"] == 20

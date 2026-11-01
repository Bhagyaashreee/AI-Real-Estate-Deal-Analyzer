import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "currency" in data
    assert data["currency"] == "INR (₹)"


def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert data["database"]["type"] == "SQLite"
    assert data["database"]["status"] == "connected"
    assert "ai_engine" in data


def test_properties_summary_endpoint():
    response = client.get("/api/v1/properties/summary")
    assert response.status_code == 200
    data = response.json()
    assert "kpis" in data
    assert data["currency"] == "INR (₹)"
    assert data["kpis"]["total_deals_analyzed"] > 0


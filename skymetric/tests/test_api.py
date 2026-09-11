"""Tests for FastAPI endpoints."""

from fastapi.testclient import TestClient
from skymetric.api.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestIndexEndpoint:
    def test_daily_index(self):
        response = client.get("/api/v1/index/daily")
        assert response.status_code == 200
        data = response.json()
        assert "headline_index" in data
        assert "sector_indices" in data
        assert "window_indices" in data

    def test_daily_index_with_date(self):
        response = client.get("/api/v1/index/daily?target_date=2026-09-01")
        assert response.status_code == 200

    def test_sector_indices(self):
        response = client.get("/api/v1/index/sectors")
        assert response.status_code == 200
        data = response.json()
        assert "sectors" in data


class TestHeatmapEndpoint:
    def test_heatmap(self):
        response = client.get("/api/v1/routes/heatmap")
        assert response.status_code == 200
        data = response.json()
        assert "corridors" in data
        assert "dates" in data
        assert "matrix" in data
        assert len(data["corridors"]) == 10

    def test_carriers(self):
        response = client.get("/api/v1/routes/carriers")
        assert response.status_code == 200
        data = response.json()
        assert "carriers" in data


class TestElasticityEndpoint:
    def test_elasticity(self):
        response = client.get("/api/v1/elasticity/")
        assert response.status_code == 200
        data = response.json()
        assert "curves" in data
        assert "advance_windows" in data

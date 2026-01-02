import pytest

pytest.importorskip("flask")

from api import rest_server
import core.cbo_scraper as cbo_scraper_module


class _FakeScraperWithCache:
    def __init__(self, use_cache=True, enable_notifications=False):
        self.cached_data = {
            "gdp": 30.0,
            "debt": 35.0,
            "deficit": 5.0,
            "revenues": {"income_tax": 2.0},
            "spending": {"healthcare": 2.5},
            "interest_rate": 4.0,
            "last_updated": "2025-01-01T00:00:00",
            "data_source": "Cache",
        }
        self.cached_data_valid = True

    def _attach_metadata(self, data, cache_used, source_tag=None, **kwargs):
        return {
            **data,
            "checksum": "cache-ck",
            "cache_used": cache_used,
            "freshness_hours": 5.0 if cache_used else 0.0,
            "cache_age_hours": 5.0 if cache_used else 0.0,
            "fetched_at": "2025-01-01T05:00:00",
            "data_source": data.get("data_source", "Cache") + (" (cache)" if cache_used else ""),
            "schema_valid": True,
            "validation_errors": [],
        }

    def get_current_us_budget_data(self):
        # Should not be called when cache is present
        raise AssertionError("Live fetch should not be called when cache exists")


class _FakeScraperLiveOnly:
    def __init__(self, use_cache=True, enable_notifications=False):
        self.cached_data = {}
        self.cached_data_valid = False

    def get_current_us_budget_data(self):
        return {
            "gdp": 31.0,
            "debt": 36.0,
            "deficit": 5.5,
            "revenues": {"income_tax": 2.1},
            "spending": {"healthcare": 2.6},
            "interest_rate": 4.0,
            "last_updated": "2025-01-02T00:00:00",
            "data_source": "Live",
            "checksum": "live-ck",
            "cache_used": False,
            "freshness_hours": 0.0,
            "cache_age_hours": 0.0,
            "fetched_at": "2025-01-02T00:00:00",
            "schema_valid": True,
            "validation_errors": [],
        }


def test_ingestion_health_uses_cache_metadata(monkeypatch):
    monkeypatch.setattr(cbo_scraper_module, "CBODataScraper", _FakeScraperWithCache, raising=False)
    app = rest_server.create_api_app()

    with app.test_client() as client:
        resp = client.get("/api/data/ingestion-health")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["status"] == "success"
        data = payload["data"]
        assert data["cache_used"] is True
        assert data["checksum"] == "cache-ck"
        assert data["freshness_hours"] == 5.0
        assert data["cache_age_hours"] == 5.0
        assert "cache" in data["data_source"].lower()


def test_ingestion_health_falls_back_to_live(monkeypatch):
    monkeypatch.setattr(cbo_scraper_module, "CBODataScraper", _FakeScraperLiveOnly, raising=False)
    app = rest_server.create_api_app()

    with app.test_client() as client:
        resp = client.get("/api/data/ingestion-health")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert payload["status"] == "success"
        data = payload["data"]
        assert data["cache_used"] is False
        assert data["checksum"] == "live-ck"
        assert data["freshness_hours"] == 0.0
        assert data["cache_age_hours"] == 0.0
        assert "live" in data["data_source"].lower()

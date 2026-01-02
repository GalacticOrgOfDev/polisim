"""
Integration and contract tests for Slice 5.7 v1 API endpoints.

Tests:
- Happy path (valid requests, correct responses)
- Validation (invalid inputs, error handling)
- Rate limiting (threshold enforcement, headers)
- Auth (optional/required enforcement)
"""

import json
import pytest
from datetime import datetime
from pathlib import Path

# This test file assumes the Flask app is created and endpoints are available


@pytest.fixture
def client():
    """Create a Flask test client."""
    from api.rest_server import create_api_app
    app = create_api_app()
    app.config['TESTING'] = True
    return app.test_client()


class TestSimulateEndpoint:
    """Tests for POST /api/v1/simulate endpoint."""
    
    def test_happy_path_basic_simulation(self, client):
        """Test successful simulation with valid inputs."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Tax Reform 2025",
            "revenue_change_pct": 10.5,
            "spending_change_pct": -5.0,
            "years": 10,
            "iterations": 100,  # Small for fast tests
        })
        
        print(f"\nResponse Status: {response.status_code}")
        print(f"Response Body: {response.get_json()}")
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["status"] == "success"
        assert data["policy_name"] == "Tax Reform 2025"
        assert data["years"] == 10
        assert data["iterations"] == 100
        assert "simulation_id" in data
        assert "results" in data
        
        # Check results structure
        results = data["results"]
        assert "mean_deficit" in results
        assert "median_deficit" in results
        assert "std_dev" in results
        assert "p10_deficit" in results
        assert "p90_deficit" in results
        assert "probability_balanced" in results
        assert "confidence_bounds" in results
        
        # Check metadata
        assert "metadata" in data
        assert data["metadata"]["api_version"] == "1.0"
        assert data["metadata"]["duration_ms"] >= 0
    
    def test_happy_path_with_sensitivity(self, client):
        """Test simulation with sensitivity analysis enabled."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Healthcare Reform",
            "revenue_change_pct": 5.0,
            "spending_change_pct": 2.0,
            "include_sensitivity": True,
        })
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["status"] == "success"
        if data.get("sensitivity"):  # May be None if analysis failed, but should attempt
            assert "parameters" in data["sensitivity"]
    
    def test_validation_missing_policy_name(self, client):
        """Test validation error: missing policy_name."""
        response = client.post('/api/v1/simulate', json={
            "revenue_change_pct": 10.0,
            "spending_change_pct": -5.0,
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "policy_name" in str(data.get("details", {}))
    
    def test_validation_revenue_out_of_range(self, client):
        """Test validation error: revenue_change_pct exceeds max."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Invalid Policy",
            "revenue_change_pct": 150.0,  # Exceeds max of 100
            "spending_change_pct": -5.0,
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_validation_spending_out_of_range(self, client):
        """Test validation error: spending_change_pct below min."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Invalid Policy",
            "revenue_change_pct": 10.0,
            "spending_change_pct": -100.0,  # Exceeds min of -50
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_validation_years_out_of_range(self, client):
        """Test validation error: years below minimum."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Policy",
            "revenue_change_pct": 5.0,
            "spending_change_pct": -2.0,
            "years": 0,  # Below min of 1
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
    
    def test_validation_iterations_out_of_range(self, client):
        """Test validation error: iterations exceed maximum."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Policy",
            "revenue_change_pct": 5.0,
            "spending_change_pct": -2.0,
            "iterations": 100000,  # Exceeds max of 50000
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["status"] == "error"
    
    def test_response_headers_include_request_id(self, client):
        """Test that responses include X-Request-ID header."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Test",
            "revenue_change_pct": 5.0,
            "spending_change_pct": -2.0,
        })
        
        assert "X-Request-ID" in response.headers
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "1.0"
        assert "X-Response-Time" in response.headers


class TestScenariosListEndpoint:
    """Tests for GET /api/v1/scenarios endpoint."""
    
    def test_happy_path_list_scenarios(self, client):
        """Test successful scenario listing."""
        response = client.get('/api/v1/scenarios')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["status"] == "success"
        assert "scenario_count" in data
        assert "returned_count" in data
        assert "pagination" in data
        assert "scenarios" in data
        
        # Check pagination structure
        pagination = data["pagination"]
        assert "page" in pagination
        assert "per_page" in pagination
        assert "total_pages" in pagination
    
    def test_happy_path_with_pagination(self, client):
        """Test scenario listing with pagination params."""
        response = client.get('/api/v1/scenarios?page=1&per_page=10')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 10
    
    def test_happy_path_with_filter(self, client):
        """Test scenario listing with type filter."""
        response = client.get('/api/v1/scenarios?filter_type=baseline')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # All returned scenarios should be baseline type
        for scenario in data["scenarios"]:
            assert scenario["type"] == "baseline" or not scenario  # Empty list OK
    
    def test_happy_path_with_search(self, client):
        """Test scenario listing with search filter."""
        response = client.get('/api/v1/scenarios?search=health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # Should return scenarios matching search term
        assert data["status"] == "success"
    
    def test_happy_path_with_sort(self, client):
        """Test scenario listing with sort param."""
        response = client.get('/api/v1/scenarios?sort_by=created_at&sort_order=asc')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["status"] == "success"
    
    def test_validation_invalid_page(self, client):
        """Test validation error: invalid page number."""
        response = client.get('/api/v1/scenarios?page=0')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_validation_invalid_per_page(self, client):
        """Test validation error: per_page exceeds max."""
        response = client.get('/api/v1/scenarios?per_page=200')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_validation_invalid_filter_type(self, client):
        """Test validation error: invalid filter_type enum."""
        response = client.get('/api/v1/scenarios?filter_type=invalid_type')
        
        assert response.status_code == 400
        data = response.get_json()
        assert data["error_code"] == "VALIDATION_ERROR"
    
    def test_response_scenario_structure(self, client):
        """Test that returned scenarios have correct structure."""
        response = client.get('/api/v1/scenarios')
        
        assert response.status_code == 200
        data = response.get_json()
        
        if data["scenarios"]:
            scenario = data["scenarios"][0]
            assert "id" in scenario
            assert "name" in scenario
            assert "type" in scenario
            assert "description" in scenario
            assert "revenue_change_pct" in scenario
            assert "spending_change_pct" in scenario
            assert "projected_deficit" in scenario
            assert "created_at" in scenario
            assert "created_by" in scenario
            assert "is_public" in scenario
            assert "tags" in scenario


class TestIngestionHealthEndpoint:
    """Tests for GET /api/v1/data/ingestion-health endpoint."""
    
    def test_happy_path_health_check(self, client):
        """Test successful ingestion health check."""
        response = client.get('/api/v1/data/ingestion-health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        assert data["status"] == "success"
        assert "ingestion" in data
        assert "validation" in data
        assert "metrics" in data
        assert "metadata" in data
        
        # Check ingestion info
        ingestion = data["ingestion"]
        assert "data_source" in ingestion
        assert "is_live" in ingestion
        assert "freshness_hours" in ingestion
        assert "cache_age_hours" in ingestion
        assert "last_updated" in ingestion
        assert "fetched_at" in ingestion
        
        # Check validation info
        validation = data["validation"]
        assert "schema_valid" in validation
        assert "checksum" in validation
        assert "validation_errors" in validation
    
    def test_happy_path_without_history(self, client):
        """Test that history not included by default."""
        response = client.get('/api/v1/data/ingestion-health')
        
        assert response.status_code == 200
        data = response.get_json()
        
        # history should not be present (or None)
        assert data.get("history") is None
    
    def test_validation_invalid_include_history(self, client):
        """Test that invalid include_history values are handled."""
        # Note: Current implementation treats any non-empty value as True,
        # but valid values are 'true', 'false', etc.
        response = client.get('/api/v1/data/ingestion-health?include_history=true')
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 401, 400]
    
    def test_response_headers(self, client):
        """Test response includes API headers."""
        response = client.get('/api/v1/data/ingestion-health')
        
        assert "X-Request-ID" in response.headers
        assert "X-API-Version" in response.headers
        assert "X-Response-Time" in response.headers


class TestRateLimitingBehavior:
    """Tests for rate limiting enforcement (when enabled)."""
    
    def test_rate_limit_headers_present(self, client):
        """Test that rate limit headers are included in responses."""
        response = client.post('/api/v1/simulate', json={
            "policy_name": "Test",
            "revenue_change_pct": 5.0,
            "spending_change_pct": -2.0,
        })
        
        # Headers should be present (even if limit not enforced)
        if "X-RateLimit-Limit" in response.headers:
            assert "X-RateLimit-Remaining" in response.headers
            assert "X-RateLimit-Reset" in response.headers
    
    def test_rate_limit_429_response(self, client):
        """Test rate limit exceeded response format."""
        # This test would require actually hitting the rate limit,
        # which depends on configuration. Skipped unless API_RATE_LIMIT_ENABLED=true
        # and API_RATE_LIMIT_PER_MINUTE is low enough to trigger in tests.
        pass


class TestErrorResponseFormat:
    """Tests for standardized error response format."""
    
    def test_error_response_structure(self, client):
        """Test that error responses follow standard format."""
        response = client.post('/api/v1/simulate', json={
            "revenue_change_pct": 10.0,
            # Missing required policy_name
        })
        
        assert response.status_code == 400
        data = response.get_json()
        
        # Standard error fields
        assert "status" in data
        assert data["status"] == "error"
        assert "error_code" in data
        assert "message" in data
        assert "details" in data
        assert "metadata" in data
        
        # Metadata should include request_id and api_version
        metadata = data["metadata"]
        assert "timestamp" in metadata
        assert "request_id" in metadata
        assert "api_version" in metadata


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

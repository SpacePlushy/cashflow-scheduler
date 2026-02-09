"""
API security feature tests for cashflow-scheduler.

Tests API security controls including:
- API key authentication
- Rate limiting behavior
- Input validation at API level
- Security headers
"""
from __future__ import annotations

import pytest
import os
import secrets as stdlib_secrets
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient


class TestAPIKeyAuthentication:
    """Test API key authentication functionality."""

    def test_api_key_comparison_uses_constant_time(self):
        """Verify that API key comparison uses secrets.compare_digest (constant-time)."""
        # Import the verify_api_key function to inspect it
        import inspect
        from api.index import verify_api_key

        # Get the source code
        source = inspect.getsource(verify_api_key)

        # Verify it uses secrets.compare_digest, not plain comparison
        assert "secrets.compare_digest" in source, "API key comparison should use secrets.compare_digest"
        assert "!=" not in source or "API_KEY" not in source.split("secrets.compare_digest")[0], \
            "Should not use != for API key comparison"

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_authentication_disabled_by_default(self):
        """When REQUIRE_API_KEY is false, authentication should be disabled."""
        from api.index import app

        client = TestClient(app)
        # Should succeed without API key when authentication is disabled
        response = client.get("/health")
        assert response.status_code == 200

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "true", "API_KEY": "test-secret-key"})
    def test_missing_api_key_returns_401(self):
        """When API key is required but missing, should return 401."""
        # Need to reload the module to pick up new env vars
        import importlib
        import api.index
        importlib.reload(api.index)

        from api.index import app
        client = TestClient(app)

        # Request without API key should fail with 401
        response = client.post("/solve", json={"plan": {}})
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "true", "API_KEY": "test-secret-key"})
    def test_invalid_api_key_returns_401(self):
        """When API key is invalid, should return 401."""
        import importlib
        import api.index
        importlib.reload(api.index)

        from api.index import app
        client = TestClient(app)

        # Request with wrong API key should fail with 401
        response = client.post(
            "/solve",
            json={"plan": {}},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "true", "API_KEY": "test-secret-key"})
    def test_valid_api_key_succeeds(self):
        """When API key is valid, request should succeed."""
        import importlib
        import api.index
        importlib.reload(api.index)

        from api.index import app
        client = TestClient(app)

        # Request with correct API key should succeed (though plan validation may fail)
        response = client.post(
            "/solve",
            json={
                "plan": {
                    "start_balance": 100,
                    "target_end": 200,
                    "band": 25,
                    "rent_guard": 1000
                }
            },
            headers={"X-API-Key": "test-secret-key"}
        )
        # Should not be 401/403 (authentication error)
        assert response.status_code != 401
        assert response.status_code != 403

    def test_error_messages_do_not_leak_information(self):
        """Missing and invalid API keys should return same error message."""
        # Both cases should return "Authentication required" to prevent enumeration
        from api.index import verify_api_key
        import inspect

        source = inspect.getsource(verify_api_key)

        # Count occurrences of "Authentication required"
        auth_required_count = source.count("Authentication required")

        # Should appear at least twice (for both missing and invalid key cases)
        assert auth_required_count >= 2, \
            "Both missing and invalid API key should return same error message"


class TestInputValidationAPI:
    """Test input validation at the API level."""

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_set_eod_validates_day_range(self):
        """set_eod should reject day values outside 1-30."""
        from api.index import app
        client = TestClient(app)

        # Day 0 should be rejected
        response = client.post("/set_eod", json={"day": 0, "eod_amount": 100})
        assert response.status_code == 400
        assert "day must be in 1..30" in response.json()["error"]

        # Day 31 should be rejected
        response = client.post("/set_eod", json={"day": 31, "eod_amount": 100})
        assert response.status_code == 400
        assert "day must be in 1..30" in response.json()["error"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_set_eod_validates_day_type(self):
        """set_eod should reject non-integer day values."""
        from api.index import app
        client = TestClient(app)

        response = client.post("/set_eod", json={"day": "invalid", "eod_amount": 100})
        assert response.status_code == 400
        assert "day must be an integer" in response.json()["error"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_set_eod_validates_amount_type(self):
        """set_eod should reject non-numeric eod_amount values."""
        from api.index import app
        client = TestClient(app)

        response = client.post("/set_eod", json={"day": 15, "eod_amount": "invalid"})
        assert response.status_code == 400
        assert "eod_amount must be a number" in response.json()["error"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_set_eod_validates_amount_range(self):
        """set_eod should reject amounts exceeding MAX_AMOUNT_CENTS."""
        from api.index import app
        from cashflow.core.model import MAX_AMOUNT_CENTS

        client = TestClient(app)
        max_dollars = MAX_AMOUNT_CENTS / 100

        # Amount exceeding max should be rejected
        response = client.post("/set_eod", json={"day": 15, "eod_amount": max_dollars + 1})
        assert response.status_code == 400
        assert "eod_amount must be between" in response.json()["error"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_export_validates_format(self):
        """export should reject invalid format values."""
        from api.index import app
        client = TestClient(app)

        response = client.post("/export", json={"format": "invalid"})
        assert response.status_code == 400
        assert "format must be md|csv|json" in response.json()["error"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_solve_validates_solver_type(self):
        """solve should reject invalid solver values."""
        from api.index import app
        client = TestClient(app)

        response = client.post("/solve", json={
            "solver": "invalid",
            "plan": {
                "start_balance": 100,
                "target_end": 200,
                "band": 25,
                "rent_guard": 1000
            }
        })
        assert response.status_code == 400
        assert "solver must be 'dp' or 'cpsat'" in response.json()["error"]


class TestSecurityHeaders:
    """Test security headers are present in responses."""

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_response_includes_x_frame_options(self):
        """Responses should include X-Frame-Options header."""
        from api.index import app
        client = TestClient(app)

        response = client.get("/health")
        assert "X-Frame-Options" in response.headers
        assert response.headers["X-Frame-Options"] == "DENY"

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_response_includes_x_content_type_options(self):
        """Responses should include X-Content-Type-Options header."""
        from api.index import app
        client = TestClient(app)

        response = client.get("/health")
        assert "X-Content-Type-Options" in response.headers
        assert response.headers["X-Content-Type-Options"] == "nosniff"

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_response_includes_csp(self):
        """Responses should include Content-Security-Policy header."""
        from api.index import app
        client = TestClient(app)

        response = client.get("/health")
        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

    @patch.dict(os.environ, {"REQUIRE_API_KEY": "false"})
    def test_response_includes_referrer_policy(self):
        """Responses should include Referrer-Policy header."""
        from api.index import app
        client = TestClient(app)

        response = client.get("/health")
        assert "Referrer-Policy" in response.headers
        assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"


class TestCORSConfiguration:
    """Test CORS configuration."""

    @patch.dict(os.environ, {"CORS_ORIGINS": ""}, clear=True)
    def test_cors_defaults_to_localhost_when_not_set(self):
        """When CORS_ORIGINS is not set, should default to localhost."""
        import importlib
        import api.index

        # Reload to pick up env changes
        importlib.reload(api.index)

        # Check that CORS_ORIGINS contains localhost defaults
        assert "http://localhost:3000" in api.index.CORS_ORIGINS

    @patch.dict(os.environ, {"CORS_ORIGINS": "https://example.com,https://other.com"})
    def test_cors_uses_environment_variable(self):
        """When CORS_ORIGINS is set, should use those origins."""
        import importlib
        import api.index

        # Reload to pick up env changes
        importlib.reload(api.index)

        # Check that CORS_ORIGINS contains configured origins
        assert "https://example.com" in api.index.CORS_ORIGINS
        assert "https://other.com" in api.index.CORS_ORIGINS

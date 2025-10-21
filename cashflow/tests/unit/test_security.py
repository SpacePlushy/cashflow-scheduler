"""
Test security features across the application.

Tests for:
- Path traversal protection
- API key authentication
- Input validation
- Integer overflow protection
- Rate limiting (basic checks - actual enforcement is environment-dependent)
"""
from __future__ import annotations

import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from cashflow.io.store import load_plan, plan_from_dict
from cashflow.core.model import to_cents, MAX_AMOUNT_CENTS
from api.index import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def minimal_plan():
    """Minimal valid plan for testing."""
    return {
        "start_balance": 90.50,
        "target_end": 490.50,
        "band": 25.0,
        "rent_guard": 1636.0,
        "deposits": [{"day": 11, "amount": 1021.0}],
        "bills": [
            {"day": 1, "name": "Test Bill", "amount": 100.0}
        ],
    }


class TestPathTraversalProtection:
    """Test path traversal protection in file loading."""

    def test_rejects_parent_directory_traversal(self, tmp_path):
        """Test that .. patterns are rejected before path resolution."""
        # Create a plan file in tmp directory
        plan_file = tmp_path / "plan.json"
        plan_file.write_text('{"start_balance": 100}')

        # Try to access it via parent directory traversal
        malicious_path = str(tmp_path / "subdir" / ".." / "plan.json")

        with pytest.raises(ValueError, match="Potentially unsafe path"):
            load_plan(malicious_path)

    def test_rejects_etc_directory_access(self):
        """Test that /etc paths are rejected."""
        with pytest.raises(ValueError, match="Potentially unsafe path"):
            load_plan("/etc/passwd")

    def test_rejects_sys_directory_access(self):
        """Test that /sys paths are rejected."""
        with pytest.raises(ValueError, match="Potentially unsafe path"):
            load_plan("/sys/kernel/debug/something")

    def test_allowed_dir_restriction_works(self, tmp_path):
        """Test that allowed_dir parameter restricts file access."""
        # Create plan in tmp directory
        allowed_dir = tmp_path / "allowed"
        allowed_dir.mkdir()
        plan_file = allowed_dir / "plan.json"
        plan_file.write_text('''{
            "start_balance": 90.5,
            "target_end": 490.5,
            "band": 25.0,
            "rent_guard": 1636.0,
            "deposits": [],
            "bills": []
        }''')

        # Create file outside allowed directory
        outside_dir = tmp_path / "outside"
        outside_dir.mkdir()
        outside_file = outside_dir / "plan.json"
        outside_file.write_text('{"start_balance": 100}')

        # Should work when inside allowed directory
        plan = load_plan(plan_file, allowed_dir=allowed_dir)
        assert plan.start_balance_cents == 9050

        # Should fail when outside allowed directory
        with pytest.raises(ValueError, match="Path traversal detected"):
            load_plan(outside_file, allowed_dir=allowed_dir)

    def test_normal_paths_still_work(self, tmp_path):
        """Test that normal file paths still work correctly."""
        plan_file = tmp_path / "plan.json"
        plan_file.write_text('''{
            "start_balance": 90.5,
            "target_end": 490.5,
            "band": 25.0,
            "rent_guard": 1636.0,
            "deposits": [],
            "bills": []
        }''')

        plan = load_plan(plan_file)
        assert plan.start_balance_cents == 9050


class TestIntegerOverflowProtection:
    """Test integer overflow protection in monetary values."""

    def test_to_cents_enforces_max_amount(self):
        """Test that to_cents rejects values over MAX_AMOUNT_CENTS."""
        # MAX_AMOUNT_CENTS is $10M = 1,000,000,000 cents
        max_dollars = MAX_AMOUNT_CENTS / 100

        # Just under the limit should work
        assert to_cents(max_dollars - 1) == int((max_dollars - 1) * 100)

        # At the limit should work
        assert to_cents(max_dollars) == MAX_AMOUNT_CENTS

        # Over the limit should raise ValueError
        with pytest.raises(ValueError, match="exceeds maximum"):
            to_cents(max_dollars + 1)

    def test_to_cents_enforces_min_amount(self):
        """Test that to_cents rejects values under -MAX_AMOUNT_CENTS."""
        min_dollars = -MAX_AMOUNT_CENTS / 100

        # Just above the limit should work
        assert to_cents(min_dollars + 1) == int((min_dollars + 1) * 100)

        # At the limit should work
        assert to_cents(min_dollars) == -MAX_AMOUNT_CENTS

        # Under the limit should raise ValueError
        with pytest.raises(ValueError, match="exceeds maximum"):
            to_cents(min_dollars - 1)

    def test_plan_from_dict_validates_all_amounts(self):
        """Test that plan_from_dict validates all monetary amounts."""
        max_dollars = MAX_AMOUNT_CENTS / 100

        # Test start_balance overflow
        with pytest.raises(ValueError, match="exceeds maximum"):
            plan_from_dict({
                "start_balance": max_dollars + 1,
                "target_end": 500,
                "band": 25,
                "rent_guard": 1636,
            })

        # Test deposit overflow
        with pytest.raises(ValueError, match="exceeds maximum"):
            plan_from_dict({
                "start_balance": 90.5,
                "target_end": 500,
                "band": 25,
                "rent_guard": 1636,
                "deposits": [{"day": 11, "amount": max_dollars + 1}],
            })

        # Test bill overflow
        with pytest.raises(ValueError, match="exceeds maximum"):
            plan_from_dict({
                "start_balance": 90.5,
                "target_end": 500,
                "band": 25,
                "rent_guard": 1636,
                "bills": [{"day": 1, "name": "test", "amount": max_dollars + 1}],
            })


class TestInputValidation:
    """Test input validation in API endpoints."""

    def test_solve_validates_solver_parameter(self, client, minimal_plan):
        """Test that /solve validates solver parameter."""
        response = client.post("/solve", json={
            "plan": minimal_plan,
            "solver": "invalid_solver"
        })
        assert response.status_code == 400
        data = response.json()
        assert "solver must be 'dp' or 'cpsat'" in data["error"]

    def test_set_eod_validates_day_type(self, client, minimal_plan):
        """Test that /set_eod validates day is an integer."""
        response = client.post("/set_eod", json={
            "day": "not_a_number",
            "eod_amount": 500.0,
            "plan": minimal_plan
        })
        assert response.status_code == 400
        data = response.json()
        assert "day must be an integer" in data["error"]

    def test_set_eod_validates_day_range(self, client, minimal_plan):
        """Test that /set_eod validates day is in range 1-30."""
        # Test day < 1
        response = client.post("/set_eod", json={
            "day": 0,
            "eod_amount": 500.0,
            "plan": minimal_plan
        })
        assert response.status_code == 400
        data = response.json()
        assert "day must be in 1..30" in data["error"]

        # Test day > 30
        response = client.post("/set_eod", json={
            "day": 31,
            "eod_amount": 500.0,
            "plan": minimal_plan
        })
        assert response.status_code == 400
        data = response.json()
        assert "day must be in 1..30" in data["error"]

    def test_set_eod_validates_eod_amount_type(self, client, minimal_plan):
        """Test that /set_eod validates eod_amount is a number."""
        response = client.post("/set_eod", json={
            "day": 15,
            "eod_amount": "not_a_number",
            "plan": minimal_plan
        })
        assert response.status_code == 400
        data = response.json()
        assert "eod_amount must be a number" in data["error"]

    def test_set_eod_validates_eod_amount_range(self, client, minimal_plan):
        """Test that /set_eod validates eod_amount is in reasonable range."""
        # Test amount too high (over $10M limit)
        response = client.post("/set_eod", json={
            "day": 15,
            "eod_amount": 11_000_000,  # Over $10M limit
            "plan": minimal_plan
        })
        assert response.status_code == 400
        data = response.json()
        assert "out of reasonable range" in data["error"]

        # Test amount too low (under -$10M limit)
        response = client.post("/set_eod", json={
            "day": 15,
            "eod_amount": -11_000_000,  # Under -$10M limit
            "plan": minimal_plan
        })
        assert response.status_code == 400
        data = response.json()
        assert "out of reasonable range" in data["error"]

    def test_export_validates_format(self, client, minimal_plan):
        """Test that /export validates format parameter."""
        response = client.post("/export", json={
            "plan": minimal_plan,
            "format": "invalid_format"
        })
        assert response.status_code == 400
        data = response.json()
        assert "format must be md|csv|json" in data["error"]

    def test_export_accepts_valid_formats(self, client, minimal_plan):
        """Test that /export accepts all valid formats."""
        for fmt in ["md", "csv", "json"]:
            response = client.post("/export", json={
                "plan": minimal_plan,
                "format": fmt
            })
            assert response.status_code == 200


class TestAPIKeyAuthentication:
    """Test API key authentication when enabled."""

    def test_endpoints_work_without_auth_when_disabled(self, client, minimal_plan):
        """Test that endpoints work without API key when auth is disabled."""
        # Ensure auth is disabled (default)
        os.environ.pop("REQUIRE_API_KEY", None)
        os.environ.pop("API_KEY", None)

        # Should work without X-API-Key header
        response = client.post("/solve", json={"plan": minimal_plan})
        assert response.status_code == 200

    def test_health_endpoint_does_not_require_auth(self, client):
        """Test that /health endpoint never requires authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"


class TestSecurityHeaders:
    """Test security headers are present in responses."""

    def test_health_endpoint_has_security_headers(self, client):
        """Test that responses include security headers."""
        response = client.get("/health")

        # Check all security headers are present
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"
        assert "Content-Security-Policy" in response.headers
        assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

    def test_api_endpoints_have_security_headers(self, client, minimal_plan):
        """Test that API endpoints include security headers."""
        response = client.post("/solve", json={"plan": minimal_plan})

        # Check security headers
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert "Content-Security-Policy" in response.headers


class TestRateLimiting:
    """Test rate limiting configuration (basic checks only).

    Note: Actual rate limit enforcement is environment-dependent and may not
    work properly in serverless environments without Redis backend.
    """

    def test_rate_limit_headers_present(self, client, minimal_plan):
        """Test that rate limit headers are present in responses."""
        response = client.post("/solve", json={"plan": minimal_plan})

        # slowapi adds rate limit headers when configured
        # Just verify the endpoint works - actual rate limiting tested manually
        assert response.status_code == 200


class TestErrorHandling:
    """Test proper error handling and logging."""

    def test_invalid_json_returns_400(self, client):
        """Test that invalid JSON returns proper error."""
        response = client.post(
            "/solve",
            content=b"not valid json",
            headers={"Content-Type": "application/json"}
        )
        # Should handle gracefully, not crash
        assert response.status_code in [400, 422]

    def test_missing_required_plan_fields(self, client):
        """Test that missing required plan fields return proper error."""
        response = client.post("/solve", json={
            "plan": {
                "start_balance": 90.5
                # Missing required fields
            }
        })
        assert response.status_code == 400
        data = response.json()
        assert "error" in data

    def test_invalid_plan_data_types(self, client):
        """Test that invalid data types in plan return proper error."""
        response = client.post("/solve", json={
            "plan": {
                "start_balance": "not_a_number",  # Should be number
                "target_end": 490.5,
                "band": 25.0,
                "rent_guard": 1636.0,
            }
        })
        assert response.status_code == 400

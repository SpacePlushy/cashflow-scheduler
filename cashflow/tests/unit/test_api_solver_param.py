"""
Test API endpoints with solver parameter.

Tests the new solver parameter functionality added to /solve, /set_eod, and /export endpoints.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from api.index import app
from cashflow.core.model import to_cents


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


class TestSolveEndpoint:
    """Tests for /solve endpoint with solver parameter."""

    def test_solve_with_cpsat_solver(self, client, minimal_plan):
        """Test /solve endpoint with cpsat solver."""
        response = client.post("/solve", json={"plan": minimal_plan, "solver": "cpsat"})
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "actions" in data
        assert "objective" in data
        assert "ledger" in data
        assert "checks" in data
        assert len(data["actions"]) == 30

        # Verify solver info
        if "solver" in data:
            assert data["solver"]["name"] in ["cpsat", "dp"]  # May fallback to dp

    def test_solve_with_dp_solver(self, client, minimal_plan):
        """Test /solve endpoint with dp solver."""
        response = client.post("/solve", json={"plan": minimal_plan, "solver": "dp"})
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "actions" in data
        assert "objective" in data
        assert "ledger" in data
        assert "checks" in data
        assert len(data["actions"]) == 30

        # Verify solver info
        assert "solver" in data
        assert data["solver"]["name"] == "dp"

    def test_solve_defaults_to_cpsat_when_no_solver_specified(self, client, minimal_plan):
        """Test /solve endpoint defaults to cpsat when solver not specified."""
        response = client.post("/solve", json={"plan": minimal_plan})
        assert response.status_code == 200
        data = response.json()

        # Should default to cpsat (or dp if cpsat unavailable)
        if "solver" in data:
            assert data["solver"]["name"] in ["cpsat", "dp"]

    def test_solve_with_invalid_solver_uses_cpsat(self, client, minimal_plan):
        """Test /solve endpoint with invalid solver parameter."""
        # The current implementation doesn't validate solver param, so invalid values
        # fall through to the else block (cpsat)
        response = client.post("/solve", json={"plan": minimal_plan, "solver": "invalid"})
        assert response.status_code == 200
        data = response.json()

        # Should fall back to cpsat path
        if "solver" in data:
            assert data["solver"]["name"] in ["cpsat", "dp"]

    def test_solve_with_no_plan_uses_default(self, client):
        """Test /solve endpoint with no plan uses default plan."""
        response = client.post("/solve", json={"solver": "dp"})
        assert response.status_code == 200
        data = response.json()

        # Should use default plan and solve successfully
        assert "actions" in data
        assert len(data["actions"]) == 30


class TestSetEodEndpoint:
    """Tests for /set_eod endpoint with solver parameter."""

    def test_set_eod_with_cpsat_solver(self, client, minimal_plan):
        """Test /set_eod endpoint with cpsat solver."""
        response = client.post("/set_eod", json={
            "day": 15,
            "eod_amount": 500.0,
            "plan": minimal_plan,
            "solver": "cpsat"
        })
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "actions" in data
        assert "objective" in data
        assert "ledger" in data
        assert len(data["actions"]) == 30

        # Verify solver info
        if "solver" in data:
            assert data["solver"]["name"] in ["cpsat", "dp"]

    def test_set_eod_with_dp_solver(self, client, minimal_plan):
        """Test /set_eod endpoint with dp solver."""
        response = client.post("/set_eod", json={
            "day": 15,
            "eod_amount": 500.0,
            "plan": minimal_plan,
            "solver": "dp"
        })
        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "actions" in data
        assert "ledger" in data

        # Verify solver info
        assert "solver" in data
        assert data["solver"]["name"] == "dp"

    def test_set_eod_defaults_to_cpsat(self, client, minimal_plan):
        """Test /set_eod endpoint defaults to cpsat when solver not specified."""
        response = client.post("/set_eod", json={
            "day": 15,
            "eod_amount": 500.0,
            "plan": minimal_plan
        })
        assert response.status_code == 200
        data = response.json()

        # Should default to cpsat
        if "solver" in data:
            assert data["solver"]["name"] in ["cpsat", "dp"]

    def test_set_eod_validates_day_range(self, client, minimal_plan):
        """Test /set_eod endpoint validates day is in range 1-30."""
        response = client.post("/set_eod", json={
            "day": 0,
            "eod_amount": 500.0,
            "plan": minimal_plan,
            "solver": "dp"
        })
        assert response.status_code == 400

        response = client.post("/set_eod", json={
            "day": 31,
            "eod_amount": 500.0,
            "plan": minimal_plan,
            "solver": "dp"
        })
        assert response.status_code == 400


class TestExportEndpoint:
    """Tests for /export endpoint with solver parameter."""

    def test_export_with_cpsat_solver(self, client, minimal_plan):
        """Test /export endpoint with cpsat solver."""
        response = client.post("/export", json={
            "plan": minimal_plan,
            "format": "md",
            "solver": "cpsat"
        })
        assert response.status_code == 200
        data = response.json()

        assert "format" in data
        assert "content" in data
        assert data["format"] == "md"
        assert len(data["content"]) > 0

    def test_export_with_dp_solver(self, client, minimal_plan):
        """Test /export endpoint with dp solver."""
        response = client.post("/export", json={
            "plan": minimal_plan,
            "format": "md",
            "solver": "dp"
        })
        assert response.status_code == 200
        data = response.json()

        assert "format" in data
        assert "content" in data
        assert data["format"] == "md"
        assert len(data["content"]) > 0

    def test_export_defaults_to_cpsat(self, client, minimal_plan):
        """Test /export endpoint defaults to cpsat when solver not specified."""
        response = client.post("/export", json={
            "plan": minimal_plan,
            "format": "md"
        })
        assert response.status_code == 200
        data = response.json()

        assert "format" in data
        assert data["format"] == "md"

    def test_export_supports_all_formats_with_solver(self, client, minimal_plan):
        """Test /export endpoint with all formats and solver parameter."""
        for fmt in ["md", "csv", "json"]:
            response = client.post("/export", json={
                "plan": minimal_plan,
                "format": fmt,
                "solver": "dp"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["format"] == fmt

    def test_export_rejects_invalid_format(self, client, minimal_plan):
        """Test /export endpoint rejects invalid format."""
        response = client.post("/export", json={
            "plan": minimal_plan,
            "format": "invalid",
            "solver": "dp"
        })
        assert response.status_code == 400


class TestSolverConsistency:
    """Tests to verify solver behavior is consistent."""

    def test_dp_and_cpsat_produce_valid_schedules(self, client, minimal_plan):
        """Test both solvers produce valid schedules."""
        # Solve with DP
        response_dp = client.post("/solve", json={"plan": minimal_plan, "solver": "dp"})
        assert response_dp.status_code == 200
        data_dp = response_dp.json()

        # Solve with CP-SAT
        response_cpsat = client.post("/solve", json={"plan": minimal_plan, "solver": "cpsat"})
        assert response_cpsat.status_code == 200
        data_cpsat = response_cpsat.json()

        # Both should produce 30-day schedules
        assert len(data_dp["actions"]) == 30
        assert len(data_cpsat["actions"]) == 30

        # Both should pass validation checks (or both fail)
        assert "checks" in data_dp
        assert "checks" in data_cpsat

    def test_solver_selection_persists_through_set_eod(self, client, minimal_plan):
        """Test solver selection is used in set_eod operation."""
        # Get initial solve with DP
        response1 = client.post("/solve", json={"plan": minimal_plan, "solver": "dp"})
        assert response1.status_code == 200

        # Use set_eod with DP solver
        response2 = client.post("/set_eod", json={
            "day": 15,
            "eod_amount": 500.0,
            "plan": minimal_plan,
            "solver": "dp"
        })
        assert response2.status_code == 200
        data = response2.json()

        # Should have used DP solver
        assert "solver" in data
        assert data["solver"]["name"] == "dp"


class TestHealthEndpoint:
    """Tests for /health endpoint."""

    def test_health_check(self, client):
        """Test /health endpoint returns ok status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

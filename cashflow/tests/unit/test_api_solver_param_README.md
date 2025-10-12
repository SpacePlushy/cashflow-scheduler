# API Solver Parameter Tests

This test suite validates the new solver parameter functionality added to the cashflow API endpoints.

## Test Coverage

### `/solve` Endpoint
- ✅ Accepts `solver=cpsat` parameter
- ✅ Accepts `solver=dp` parameter
- ✅ Defaults to `cpsat` when no solver specified
- ✅ Handles invalid solver values (falls back to cpsat path)
- ✅ Returns correct solver info in response

### `/set_eod` Endpoint
- ✅ Accepts `solver` parameter for both CP-SAT and DP
- ✅ Defaults to `cpsat` when no solver specified
- ✅ Validates day range (1-30)
- ✅ Applies correct solver in the re-solve operation

### `/export` Endpoint
- ✅ Accepts `solver` parameter for all formats (md, csv, json)
- ✅ Defaults to `cpsat` when no solver specified
- ✅ Rejects invalid format values

### Cross-cutting Concerns
- ✅ Both solvers produce valid 30-day schedules
- ✅ Solver selection persists through operations
- ✅ Health check endpoint works correctly

## Running the Tests

```bash
# Run just these tests
pytest cashflow/tests/unit/test_api_solver_param.py -v

# Run with coverage
pytest cashflow/tests/unit/test_api_solver_param.py --cov=api --cov-report=term-missing

# Run specific test class
pytest cashflow/tests/unit/test_api_solver_param.py::TestSolveEndpoint -v
```

## Dependencies

The tests require:
- `pytest` (already in requirements.txt)
- `fastapi` (already in requirements.txt)
- `httpx` (installed with FastAPI for TestClient support)

## Test Structure

Tests use FastAPI's TestClient to make synchronous HTTP requests to the API endpoints without requiring a running server. Each test:

1. Creates a test client fixture
2. Sends requests with various solver parameter combinations
3. Validates response status codes
4. Checks response structure and solver info

## Known Issues

- Invalid solver values currently fall through to the cpsat path instead of returning a 400 error
  - This is documented in the code review comment
  - Tests verify current behavior but note it should be improved

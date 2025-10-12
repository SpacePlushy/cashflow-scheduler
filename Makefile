.PHONY: setup setup-dev lint type test format verify smoke smoke-vercel web-install web-dev web-build web-lint web-start clean
# Use python -m pip for portability across environments where `pip` may not be on PATH
setup: ; python3 -m pip install -r requirements.txt
setup-dev: ; python3 -m pip install -e .
lint: ; ruff check cashflow && black --check cashflow
type: ; mypy cashflow
test: ; pytest -q
format: ; black cashflow && ruff check cashflow --fix
verify: ; python -m cashflow.cli verify
smoke: ; UI_URL=$(UI_URL) API_URL=$(API_URL) VERIFY_URL=$(VERIFY_URL) BYPASS=$(BYPASS) node scripts/smoke.mjs
smoke-vercel: ; bash scripts/vercel_smoke.sh --ui-project $(UI_PROJECT) --api-project $(API_PROJECT) --ui-url $(UI_URL) $(if $(API_URL),--api-url $(API_URL),) $(if $(VERIFY_URL),--verify-url $(VERIFY_URL),) $(if $(TEAM),--team $(TEAM),)

web-install: ; cd web && npm install
web-dev: ; cd web && npm run dev
web-build: ; cd web && npm run build
web-start: ; cd web && npm run start
web-lint: ; cd web && npm run lint

clean: ; find . -type d -name __pycache__ -exec rm -rf {} + ; find . -type f -name '*.pyc' -delete ; rm -rf .pytest_cache .mypy_cache *.egg-info build dist

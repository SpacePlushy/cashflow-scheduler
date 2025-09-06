.PHONY: setup lint type test format verify smoke smoke-vercel
setup: ; pip install -r requirements.txt
lint: ; ruff check cashflow && black --check cashflow
type: ; mypy cashflow
test: ; pytest -q
format: ; black cashflow && ruff check cashflow --fix
verify: ; python -m cashflow.cli verify
smoke: ; UI_URL=$(UI_URL) API_URL=$(API_URL) VERIFY_URL=$(VERIFY_URL) BYPASS=$(BYPASS) node scripts/smoke.mjs
smoke-vercel: ; bash scripts/vercel_smoke.sh --ui-project $(UI_PROJECT) --api-project $(API_PROJECT) --ui-url $(UI_URL) $(if $(API_URL),--api-url $(API_URL),) $(if $(VERIFY_URL),--verify-url $(VERIFY_URL),) $(if $(TEAM),--team $(TEAM),)

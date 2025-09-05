.PHONY: setup lint type test format verify
setup: ; pip install -r requirements.txt
lint: ; ruff check cashflow && black --check cashflow
type: ; mypy cashflow
test: ; pytest -q
format: ; black cashflow && ruff check cashflow --fix
verify: ; python -m cashflow.cli verify
smoke: ; UI_URL=$(UI_URL) API_URL=$(API_URL) VERIFY_URL=$(VERIFY_URL) BYPASS=$(BYPASS) node scripts/smoke.mjs

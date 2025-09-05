.PHONY: setup lint type test format verify api serve dev ui ui-install ui-build ui-preview
setup: ; pip install -r requirements.txt
lint: ; ruff check cashflow && black --check cashflow
type: ; mypy cashflow
test: ; python -m pytest -q
format: ; black cashflow && ruff check cashflow --fix
verify: ; python -m cashflow.cli verify
api: ; uvicorn cashflow.api.app:app --reload --host 127.0.0.1 --port 8000
serve: ; uvicorn cashflow.api.app:app --host 127.0.0.1 --port 8000
ui-install: ; cd ui && npm install
ui: ; cd ui && npm run dev
ui-build: ; cd ui && npm run build
ui-preview: ; cd ui && npm run preview
dev: ; echo "Run 'make api' and 'make ui' in separate terminals"

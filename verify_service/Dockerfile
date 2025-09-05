FROM python:3.11-slim

WORKDIR /app

# System deps (optional; keep slim)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Copy repo and install the core package
COPY . /app
RUN pip install --no-cache-dir -r verify_service/requirements.txt \
    && pip install --no-cache-dir -e .

EXPOSE 8000
CMD ["uvicorn", "verify_service.app:app", "--host", "0.0.0.0", "--port", "8000"]

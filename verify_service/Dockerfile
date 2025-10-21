FROM python:3.11-slim

WORKDIR /app

# System deps (optional; keep slim)
RUN apt-get update && apt-get install -y --no-install-recommends build-essential && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd -m -u 1000 -s /bin/bash appuser && \
    chown -R appuser:appuser /app

# Copy only needed files (not entire repo)
COPY --chown=appuser:appuser requirements.txt .
COPY --chown=appuser:appuser pyproject.toml .
COPY --chown=appuser:appuser cashflow/ ./cashflow/
COPY --chown=appuser:appuser verify_service/ ./verify_service/

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir -e .

# Switch to non-root user
USER appuser

EXPOSE 8080
CMD ["uvicorn", "verify_service.app:app", "--host", "0.0.0.0", "--port", "8080"]

# ──────────────────────────────────────────────────────────────────────
# WhatsApp AI Receptionist – Dockerfile
# ──────────────────────────────────────────────────────────────────────

# ── Stage 1: dependency builder ────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build essentials for packages that need compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: runtime image ────────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root user for security
RUN useradd --create-home appuser
WORKDIR /home/appuser/app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Copy application source
COPY --chown=appuser:appuser . .

USER appuser

# Expose the application port (default 8000, overridable via APP_PORT)
EXPOSE 8000

# Use environment variable for port so it can be overridden at runtime
ENV APP_HOST=0.0.0.0 \
    APP_PORT=8000 \
    LOG_LEVEL=INFO

CMD ["sh", "-c", "uvicorn main:app --host $APP_HOST --port $APP_PORT --log-level $(echo $LOG_LEVEL | tr '[:upper:]' '[:lower:]')"]

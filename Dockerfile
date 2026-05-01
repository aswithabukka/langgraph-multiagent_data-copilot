# syntax=docker/dockerfile:1.6
# ---- builder stage ----
FROM python:3.11-slim AS builder

WORKDIR /build

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps live in this stage only.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
# Build wheels for all runtime deps (fast install in the runtime stage).
RUN pip install --upgrade pip && \
    pip wheel --wheel-dir=/wheels .

# ---- runtime stage ----
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install pre-built wheels — no compilers in the runtime image.
COPY --from=builder /wheels /wheels
COPY pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install --no-index --find-links=/wheels . && \
    rm -rf /wheels

# Copy source after deps so layer caching works on code-only changes.
COPY app ./app
COPY ui ./ui
COPY scripts ./scripts
COPY main.py start_services.py ./

# Create chart dir and a non-root user, then drop privileges.
RUN mkdir -p /app/charts && \
    useradd --create-home --shell /usr/sbin/nologin appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/').status==200 else 1)" || exit 1

CMD ["python", "main.py"]

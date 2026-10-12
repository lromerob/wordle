# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS dependencies
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY requirements.lock ./
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --only-binary=:all: --require-hashes -r requirements.lock

FROM python:3.12-slim-bookworm AS runtime-base
ENV PATH="/opt/venv/bin:$PATH" PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --gid 10001 app && useradd --uid 10001 --gid app --no-create-home app
WORKDIR /app
COPY --from=dependencies /opt/venv /opt/venv
COPY --chown=10001:10001 app/ ./app/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1", "--no-proxy-headers"]

# Explicit local-test target; not included in the production runtime target.
FROM runtime-base AS memory-test
COPY --chown=10001:10001 tests/test_backend.py /opt/test-support/test_backend.py
COPY --chown=10001:10001 docker/memory_server.py /opt/test-support/memory_server.py
CMD ["python", "/opt/test-support/memory_server.py"]

# Default build is production: no test fixtures or memory entrypoint.
FROM runtime-base AS runtime

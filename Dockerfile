FROM python:3.12-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2 AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m pip install --no-cache-dir build \
    && python -m build --wheel --outdir /dist

FROM python:3.12-slim-bookworm@sha256:4766d8b510c428e595d74b9cc5bbb2fae8e26316fffb4adc89908d79aacd58a2 AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --gid 10001 specforge \
    && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin specforge

COPY --from=builder /dist /dist
RUN set -eu; \
    wheel="$(find /dist -maxdepth 1 -name '*.whl' -print -quit)"; \
    test -n "$wheel"; \
    python -m pip install --no-cache-dir "${wheel}[api]"; \
    rm -rf /dist

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=5 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).read()"]

CMD ["python", "-m", "uvicorn", "specforge_gate.api:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

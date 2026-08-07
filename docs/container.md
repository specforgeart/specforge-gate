# Docker image and Compose

SpecForge Gate includes a minimal container deployment for the existing REST API and web UI. It does not add another application layer: the container starts `specforge_gate.api:app`, so `GET /`, `GET /healthz`, and `POST /v1/check` keep the same behavior and contracts as the non-container API process.

## Start with Docker Compose

```bash
docker compose up --build -d --wait
```

Open `http://127.0.0.1:8000/` for the web UI or call `http://127.0.0.1:8000/healthz`. Stop and remove the container with:

```bash
docker compose down --remove-orphans
```

The default host bind is loopback-only. To use another local port without editing the file:

```bash
SPECFORGE_PORT=8080 docker compose up --build -d --wait
```

PowerShell:

```powershell
$env:SPECFORGE_PORT = "8080"
docker compose up --build -d --wait
```

## Image design

The `Dockerfile` uses a multi-stage build. The builder creates the project wheel; the runtime stage installs that wheel with the existing `api` extra and contains no source checkout or development dependency set. The service:

- runs as a non-root UID/GID `10001`;
- disables Python bytecode writes;
- has a healthcheck against the existing `/healthz` endpoint;
- disables Uvicorn access logs so pasted request content cannot appear there;
- exposes only container port `8000`.

The Compose profile adds runtime hardening:

- host publishing is `127.0.0.1` by default rather than every interface;
- a read-only root filesystem is enforced;
- `/tmp` is a small ephemeral `tmpfs`;
- all Linux capabilities are dropped;
- `no-new-privileges` is enabled;
- no host directory or persistent volume is mounted.

## Security boundary

Containerization does not add authentication, TLS termination, rate limiting, persistence, uploads, a database, or a reverse proxy. Keep loopback binding for local demos. If the service is intentionally exposed outside the host, put an appropriate authenticated TLS-terminating proxy or hosting layer in front of it.

The image build requires network access to obtain the Python base image and package dependencies. At runtime the deterministic analysis path still makes no outbound provider call.

## Verification

Canonical Python checks validate the Docker/Compose contracts statically. GitHub-hosted Linux CI additionally runs `docker compose config`, builds the image, starts the service, waits for the container healthcheck, verifies `/healthz`, the web UI, and a deterministic `/v1/check` response, confirms the process runs as UID `10001`, and tears the service down. The existing stable `ci-gate` aggregates this container smoke job, so branch-protection context names do not change.

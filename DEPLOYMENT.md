# Deployment

## 1. Requirements

- Linux or another Docker-supported host for the container workflow.
- Docker Engine and the Docker Compose v2 plugin (`docker compose`).
- Python 3.13 or newer and `uv` only when running the Makefile targets directly on the host.
- Network access from the API container to a provisioned MySQL-compatible database, Redis, the configured SMTP server, and any external APIs used by the enabled application features.
- The database and required runtime data must be provisioned separately. The repository includes an Alembic baseline migration but no database service or reference-data initialization.

The root `README.md` says this repository is illustrative and does not include the data, frontend, or configuration needed for a turnkey installation.

## 2. Environment Configuration

### Local Compose

`docker-compose.dev.yml` explicitly loads a root `.env` file into the `api` container. Compose also interpolates selected values from that file. `.env.example` is a variable-name/example template generated from `app/core/config.py`; its blank values and redacted database URL are not usable credentials. Copy it and replace the required values with values issued for the target environment:

```sh
cp .env.example .env
```

The application reads settings from environment variables. Compose injects `.env`; the production image has no `.env` file configured by its Dockerfile, so its runtime environment must be supplied by the deployment environment.

Required settings declared without defaults by `app/core/config.py` are:

- `COOKIE_PASSWORD`
- `BUY_FILLING_SECRET`
- `HIDDEN_CAPTCHA_SECRET`
- `EMAIL_UNSUBSCRIBE_SECRET`
- `SERVER_SECRET_KEY`
- `DATABASE_URL`
- `SIGNATURE_SECRET`
- `CRYPTOMUS_SECRET_KEY`
- `PROMETHEUS_LOGIN`
- `PROMETHEUS_PASSWORD`
- `MAIL_PASSWORD`

Provide strong, environment-specific secrets. Do not copy example or test secrets into a deployed environment. `DATABASE_URL` must use the async MySQL driver available in the project (`aiomysql`) and point to an already-provisioned database. Configure `REDIS_URL` to a Redis instance reachable from inside the container; its application default is `redis://localhost/0`, which refers to the API container itself in Docker.

Other settings control origins and URLs, locale support, database-independent application behavior, email delivery, GeoIP files, Redis startup behavior, Cryptomus credentials and callback configuration, and Prometheus. Their defaults are in `app/core/config.py`; configure values appropriate to the target environment. Email delivery requires a reachable SMTP server and the corresponding `MAIL_*` settings. Cryptomus operations require merchant/API credentials and a callback URL reachable by Cryptomus.

## 3. Local Development

Start from a checkout of this repository. The checked-in Compose file is `docker-compose.dev.yml`; it starts only the API and does not start MySQL or Redis. Provision those separately and set reachable addresses and credentials in `.env`.

From the repository root:

```sh
cp .env.example .env
# Edit .env with the required settings and reachable external service URLs.
docker compose -f docker-compose.dev.yml up --build
```

The API listens on port `8000` inside the container and Compose publishes it on host port `8000`. In a second terminal, check the route:

```sh
curl --fail http://localhost:8000/ping
```

The expected response is JSON containing `"ping":"pong!!"`. This route only confirms that the API handled the request; it does not verify its database or Redis connections.

Stop the foreground Compose process with `Ctrl-C`. To start detached instead, use:

```sh
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml logs -f api
docker compose -f docker-compose.dev.yml down
```

## 4. Docker

`Dockerfile` uses a multi-stage build based on `python:3.13-slim-bookworm`. Its builder installs `uv`, syncs dependencies from `pyproject.toml` and `uv.lock`, and the final stage copies the virtual environment and application source. The final image has no `ENTRYPOINT` or `CMD`; the development Compose file supplies the Uvicorn command.

The only checked-in Compose file is `docker-compose.dev.yml`:

- Service: `api`.
- Published port: `8000:8000`.
- Bind mounts: `./app:/app/app` and `./tests:/app/tests`.
- Extra host mapping: `host.docker.internal:host-gateway`.
- No active database or Redis service, named volume, or custom network is defined. A Redis service and volume are present only as commented-out YAML.
- There are no Compose `depends_on` declarations or container health checks.

To build the image without starting the development service:

```sh
docker build -t payback-api .
```

The production Docker build uses the Dockerfile's default dependency-group argument and explicitly includes the `lint` group. The development Compose build adds the `dev` group as well.

## 5. Database

The application connects using `DATABASE_URL` through SQLAlchemy's asynchronous engine and `aiomysql`. No database container or schema bootstrap command is defined in this repository.

The application does not apply migrations at startup. The Docker image includes Alembic. With `.env` configured and the image rebuilt to include the migration files, apply the initial schema to an empty database with:

```sh
docker compose -f docker-compose.dev.yml build api
docker compose -f docker-compose.dev.yml run --rm api alembic upgrade head
```

This first revision is a baseline snapshot that creates the current ORM tables. It is intended for a new, empty database. For an existing database, compare its schema to the baseline first; if it already matches, record the baseline without executing it:

```sh
docker compose -f docker-compose.dev.yml run --rm api alembic stamp head
```

Do not run `upgrade head` on an existing populated database before stamping it; the initial revision attempts to create those tables. Future schema changes should be added as new revisions. This repository does not initialize application-specific reference data.

For tests, configure `DATABASE_URL` to a dedicated test database with the required schema. Do not point integration tests at production data.

## 6. Tests

The repository's canonical full test command is:

```sh
make test
```

The Makefile's `bootstrap` target installs/synchronizes the `lint` and `dev` dependency groups with `uv`; the test target runs `pytest --cov=app` and writes terminal and XML coverage reports. The database-backed integration tests require a reachable test database configured through `DATABASE_URL`. Tests that exercise Redis or other external behavior require their configured dependencies or test doubles.

Test directories can be run separately after `make bootstrap`:

```sh
uv run pytest tests/api/
uv run pytest tests/services/
uv run pytest tests/repositories/
uv run pytest tests/integration/
uv run pytest tests/utils/
```

The `tests/integration` group uses the configured database. There is no separate test database container in the Compose file.

## 7. Linting and Formatting

Use the Makefile targets:

```sh
make lint
```

This runs `uv run ruff check .` and `uv run mypy .` after synchronizing the `lint` and `dev` dependency groups. To run each check separately:

```sh
uv run ruff check .
uv run mypy .
```

The Makefile does not define a Ruff formatting command.

## 8. Production Deployment

The repository does not define a complete production deployment command or environment. It has no production Compose file, Kubernetes manifests, deployment script, or runtime `CMD` in the Dockerfile. Production infrastructure must provide the application environment, external database and Redis, SMTP configuration, required runtime data, and an explicit Uvicorn startup command.

The production operator must run `alembic upgrade head` using the built application image and the production `DATABASE_URL` before starting a release that requires schema changes. This repository does not define the target runtime, environment injection, or production rollout command. The Dockerfile builds an image but does not launch the API because it defines no runtime command.

## 9. Updating / Redeployment

For local development, rebuild and restart the Compose API:

```sh
docker compose -f docker-compose.dev.yml up --build -d
docker compose -f docker-compose.dev.yml logs --tail=100 api
curl --fail http://localhost:8000/ping
```

For production, this repository does not define a command sequence that updates a running service. Follow the deployment procedure for the target environment and verify its image, runtime environment, schema compatibility, restart strategy, and health checks there.

## 10. Rollback

No automated rollback procedure or production runtime configuration is defined in this repository. A rollback can only be performed through the external deployment system if it retains a previously deployed image and supports restoring it. Alembic revisions have downgrade operations, but this initial baseline downgrade drops all tables and therefore deletes their data; do not use it to roll back a populated database. Confirm compatibility and back up the external database according to its owner/operator procedures before schema changes.

## 11. Health Checks / Verification

The application exposes `GET /ping`, returning `{"ping":"pong!!"}`. There is no Docker or Compose health check, and the route does not probe external dependencies.

For the local Compose service:

```sh
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml logs --tail=100 api
curl --fail http://localhost:8000/ping
```

The application checks Redis during startup when `REDIS_STARTUP_CHECK=true` (the development Compose file sets it to `false`). Startup does not issue a database health check. Verify database and Redis connectivity through deployment-specific monitoring or application operations; no dedicated readiness endpoint is defined.

## 12. Troubleshooting

| Symptom | Cause indicated by the repository | Action |
|---|---|---|
| Container exits before serving requests with a settings validation error | One or more required environment values are absent, including `DATABASE_URL`, application secrets, Prometheus credentials, or `MAIL_PASSWORD`. | Check the API's effective environment and fill the required fields in `.env`; do not use blank example values. |
| API starts but database-backed operations fail | The Compose file does not start a database, and the configured database may not be reachable or provisioned with the expected schema. | Check `DATABASE_URL`, database reachability from the container, and schema provisioning with the database operator. |
| Redis-dependent behavior fails although `/ping` responds | `/ping` does not test Redis; development Compose disables the startup Redis check and does not start a Redis service. | Set `REDIS_URL` to a reachable Redis endpoint and inspect `docker compose -f docker-compose.dev.yml logs api`. |
| Startup fails while Redis startup checking is enabled | `REDIS_STARTUP_CHECK` defaults to true; startup connects to Redis and loads burning-email data. | Check `REDIS_URL`, Redis availability, and the `app/utils/misc/burning_emails.py` startup loader. |
| Recovery or payment email delivery fails | SMTP is external and `MAIL_PASSWORD` is required; other mail connection settings come from `MAIL_*`. | Verify SMTP reachability and the configured `MAIL_*` values without exposing credentials in logs or support output. |

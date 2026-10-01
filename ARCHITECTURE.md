# Architecture

## Scope

This repository contains the backend API.

## Request flow

`app/main.py` creates the FastAPI application, installs CORS and locale middleware, registers the localized exception handler, and includes the routes from `app/api/router.py`.

The API router currently exposes:

- VPN purchase, tariff, filling, cookie, and recovery endpoints from `app/api/v1/vpn/buy.py` and `recovery.py`.
- Common payment success, failure, and coupon endpoints from `app/api/v1/vpn/payment/payment.py`.
- Cryptomus payment creation and callback endpoints from `app/api/v1/vpn/payment/cryptomus.py`.
- The code for other payment systems (eg. Stripe), except Cryptomus, was removed from the public GitHub demo because it contains my own proprietary work, but can be disclosed upon personal request. Cryptomus was retained because it simply follows the payment provider's documentation.
- Administrative server endpoints from `app/api/v1/admin/servers.py`.
- `GET /ping` from `app/api/v1/system.py`.

Several VPN and payment routes are registered both with and without a `/{lang}` URL prefix. FastAPI dependencies provide services and repositories to route handlers.

## Application layers

- **API (`app/api`)** receives HTTP requests, validates inputs through `app/schemas`, invokes services, and returns response models.
- **Services (`app/services`)** implement application workflows, including purchases, Cryptomus payments, subscriptions, account recovery, email, and server updates.
- **Domain (`app/domain`)** contains application data models and domain types that are passed between layers.
- **Repositories (`app/repositories`)** read and write persistence data using SQLAlchemy statements and sessions.
- **ORM models (`app/models`)** map database tables using SQLAlchemy 2.x typed declarative mappings.
- **Core and utilities (`app/core`, `app/utils`, `app/middlewares`)** provide configuration, database and Redis clients, localization, logging, authentication, and shared helpers.

## Persistence and external services

`app/core/database.py` creates an asynchronous SQLAlchemy engine from `DATABASE_URL` and an `async_sessionmaker`. Repositories obtain sessions through this module. Alembic uses the same async MySQL URL and the metadata from `app/models` for schema migrations. The initial revision is a baseline for the current tables; later schema changes should be added as new revisions.

`app/core/redis.py` creates the Redis client from `REDIS_URL`. Redis is used by application workflows including access-code recovery, rate limiting, and startup data loading. Email is sent through the configured SMTP service. Cryptomus is the active payment-provider integration.

## Startup and shutdown

The FastAPI lifespan in `app/main.py` optionally connects to Redis and loads burning-email data when `REDIS_STARTUP_CHECK` is enabled. It also initializes the translation service, whose locale files are loaded lazily from `app/locales/`. On shutdown, it closes Redis and disposes the SQLAlchemy engine.

The `/ping` route returns a small API response; it does not check database or Redis connectivity.

## Tests

Tests are organized under `tests/api`, `tests/services`, `tests/repositories`, `tests/integration`, and `tests/utils`. Integration tests use the configured database URL and a non-pooled SQLAlchemy engine; use a test database with the required schema rather than a production database.

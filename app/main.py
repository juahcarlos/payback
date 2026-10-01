from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.router import api_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import LocalizedAPIException
from app.core.logs import log
from app.core.redis import redis_manager
from app.middlewares import locale_middleware
from app.services import TranslationService, get_translation_service
from app.utils.auth import get_current_username
from app.utils.misc.burning_emails import load_burning_emails


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.prometheus_enabled:
        instrumentator.expose(
            app,
            dependencies=[Depends(get_current_username)],
        )
        log.debug("Prometheus metrics exposed.")

    if settings.redis_startup_check:
        redis_client = await redis_manager.connect()
        if await redis_client.ping():  # type: ignore[misc]
            log.debug("Redis connected")
        else:
            log.warning("No Redis connection")

        await load_burning_emails(redis=redis_client)
    else:
        log.info("Redis startup check skipped")

    app.state.i18n = TranslationService(locales_path=Path(__file__).parent / "locales")
    log.debug("Locales are ready to load lazily.")

    yield

    await redis_manager.close()
    await engine.dispose()
    log.debug("Redis connection closed.")


app = FastAPI(lifespan=lifespan)

app.include_router(api_router)


if settings.prometheus_enabled:
    instrumentator = Instrumentator().instrument(app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.middleware("http")(locale_middleware)


@app.exception_handler(LocalizedAPIException)
async def localized_exception_handler(
        request: Request,
        exc: LocalizedAPIException,
) -> JSONResponse:
    i18n = get_translation_service(request)

    locale = request.state.user_locale

    translated_message = (
        i18n.translate_message(exc.system_error_code, locale)
        or "Unknown Error"  # TODO: translate!
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.system_error_code,
            "error_msg": translated_message,
            "status": exc.system_error_category,
        }
    )

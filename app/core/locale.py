from fastapi import Request

from app.core.config import settings


def get_current_locale(request: Request) -> str:
    return getattr(request.state, "user_locale", settings.default_locale)

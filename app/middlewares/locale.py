from fastapi import Request

from app.core.config import settings


def extract_locale(
        request: Request,
        path_locale: str | None = None,
        query_locale: str | None = None,
) -> str:
    if path_locale in settings.supported_locales:
        return path_locale

    if query_locale in settings.supported_locales:
        return query_locale

    header_locale = request.headers.get("Accept-Language", "").split(",")[0]
    if header_locale in settings.supported_locales:
        return header_locale

    return settings.default_locale


async def locale_middleware(request: Request, call_next):
    path_locale = request.path_params.get(settings.locale_param_name)
    query_locale = request.query_params.get(settings.locale_param_name)

    user_locale = extract_locale(
        request=request,
        path_locale=path_locale,
        query_locale=query_locale,
    )

    request.state.user_locale = user_locale

    response = await call_next(request)
    return response

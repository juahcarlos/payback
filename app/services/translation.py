import json
from pathlib import Path
from typing import cast

from fastapi import Request


# TODO: make it get locale, without passing it explicitly?

class TranslationService:
    def __init__(self, locales_path: Path):
        self.locales_path = locales_path

        self._cache: dict[str, dict[str, str]] = {}

    def _load_translations_from_file(self, locale: str) -> dict[str, str]:
        file_path = self.locales_path / f"{locale}.json"

        with open(file_path, encoding="utf-8") as f:
            data: dict[str, str] = json.load(f)

        return data

    def _get_translations(self, locale: str | None) -> dict[str, str]:
        if not locale:
            locale = "en"

        if locale in self._cache:
            return self._cache[locale]

        try:
            data = self._load_translations_from_file(locale)
        except (FileNotFoundError, ValueError):
            if locale == "en":
                raise
            data = self._get_translations("en")

        self._cache[locale] = data

        return data

    def translate_message(self, key: str, locale: str | None = "en") -> str:
        translations = self._get_translations(locale)
        message = translations.get(key)
        if not message:
            translations = self._get_translations("en")
            message = translations.get(key)

        return message or "UNKNOWN"


def get_translation_service(request: Request) -> TranslationService:
    return cast(TranslationService, request.app.state.i18n)

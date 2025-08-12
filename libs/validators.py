from config import settings
from libs.exceptions import internal_error


def check_lang(lang: str = "en") -> str:
    if lang not in settings.LANGS:
        raise internal_error("en", f"lang {lang} is not supported")
    return lang

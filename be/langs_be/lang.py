import json

from config import settings


def get_lang(lang):
    with open(f"langs/{lang}.json", "r") as f:
        text = f.read()
        res = json.loads(text)
        return res


langs_ = settings.LANGS


def get_langs():
    lang_data = {}
    for lang in langs_:
        lang_data[lang] = get_lang(lang)
    return lang_data


def langs(lang, key):
    if key not in get_lang(lang).keys():
        lang = "en"
    return get_lang(lang).get(key, "")

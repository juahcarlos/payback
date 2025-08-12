import json

from config import settings
from dbm.redis_db import rdb
from libs.logs import log


def get_lang(lang):
    with open(f"../langs/{lang}.json", "r") as f:
        text = f.read()
        res = json.loads(text)
        return res


langs_ = settings.LANGS


def get_langs():
    lang_data = rdb.hgetall("lang_data")
    for lang in langs_:
        lang_data[lang] = get_lang(lang)
    rdb.hset("lang_data", lang_data)
    rdb.expire("lang_data", 600)
    return lang_data


def langs(lang, key):
    if key not in get_lang(lang).keys():
        log.debug(f"There is no value in langs lang {lang} for key {key}")
        lang = "en"
    return get_lang(lang).get(key, "")

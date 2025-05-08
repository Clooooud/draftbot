import importlib
from settings import LANGUAGE

lang_module = f"lang.{LANGUAGE}" if LANGUAGE in ["fr", "en"] else "lang.en"
lang = importlib.import_module(lang_module)

def translate(key, **kwargs):
    """
    Translate a key using the selected language module.
    """
    translation = getattr(lang, key, key)
    for k, v in kwargs.items():
        translation = translation.replace("{{" + k + "}}", str(v))
    return translation


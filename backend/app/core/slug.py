"""Слаги без внешних зависимостей: транслитерация кириллицы (ГОСТ-подобная), латиница, цифры и дефисы."""

import re
import unicodedata

_RU = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def slugify(value: str, max_length: int = 200) -> str:
    text = unicodedata.normalize("NFKD", str(value or "")).lower()
    out = []
    for ch in text:
        if ch in _RU:
            out.append(_RU[ch])
        elif ch.isascii() and (ch.isalnum()):
            out.append(ch)
        elif unicodedata.category(ch).startswith("M"):
            continue  # диакритика после NFKD
        else:
            out.append("-")
    slug = re.sub(r"-{2,}", "-", "".join(out)).strip("-")
    return slug[:max_length].strip("-")

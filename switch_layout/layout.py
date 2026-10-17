"""Преобразование русской и английской раскладки."""

import re
from typing import Literal

from switch_layout.exceptions import ConversionError

Direction = Literal["en-ru", "ru-en"]

# Символы в одной позиции соответствуют одной физической клавише.
EN_LOWER = "`qwertyuiop[]asdfghjkl;'zxcvbnm,./"
RU_LOWER = "ёйцукенгшщзхъфывапролджэячсмитьбю."
EN_UPPER = '~QWERTYUIOP{}ASDFGHJKL:"ZXCVBNM<>?'
RU_UPPER = "ЁЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮ,"
# Дополнительные сочетания Shift + цифра, различающиеся у RU и EN.
EN_EXTRA = "@#$^&"
RU_EXTRA = '"№;:?'

EN_TO_RU = str.maketrans(
    EN_LOWER + EN_UPPER + EN_EXTRA,
    RU_LOWER + RU_UPPER + RU_EXTRA,
)
RU_TO_EN = str.maketrans(
    RU_LOWER + RU_UPPER + RU_EXTRA,
    EN_LOWER + EN_UPPER + EN_EXTRA,
)

CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
LATIN_RE = re.compile(r"[A-Za-z]")


def detect_direction(text: str) -> Direction:
    """Выбрать направление по преобладающему алфавиту."""
    if not isinstance(text, str) or not text.strip():
        raise ConversionError("Буфер обмена пуст.")

    cyrillic_count = len(CYRILLIC_RE.findall(text))
    latin_count = len(LATIN_RE.findall(text))

    if cyrillic_count == 0 and latin_count == 0:
        raise ConversionError("В тексте нет русских или английских букв.")
    if cyrillic_count == latin_count:
        raise ConversionError(
            "Невозможно определить раскладку: поровну русских и английских букв."
        )
    if latin_count > cyrillic_count:
        return "en-ru"
    return "ru-en"


def convert_layout(text: str) -> str:
    """Переключить раскладку текста, сохранив регистр букв."""
    direction = detect_direction(text)
    table = EN_TO_RU if direction == "en-ru" else RU_TO_EN
    return text.translate(table)

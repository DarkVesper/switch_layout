import pytest

from switch_layout.exceptions import ConversionError
from switch_layout.layout import convert_layout, detect_direction


@pytest.mark.parametrize(
    ("original", "expected"),
    [
        ("ghbdtn", "привет"),
        ("Привет", "Ghbdtn"),
        ("Ghbdtn!", "Привет!"),
        ("ПРИВЕТ", "GHBDTN"),
        ("Ёж", "~;"),
        ("123 ghbdtn!", "123 привет!"),
        ("z", "я"),
        ("я", "z"),
        ("Rfr ltkf", "Как дела"),
    ],
)
def test_convert_layout(original, expected):
    assert convert_layout(original) == expected


def test_detect_directions():
    assert detect_direction("ghbdtn") == "en-ru"
    assert detect_direction("привет") == "ru-en"
    assert detect_direction("ghbdtn я") == "en-ru"
    assert detect_direction("привет a") == "ru-en"


@pytest.mark.parametrize("text", ["", " \n\t", "123 !!!", "🙂", "aя"])
def test_invalid_input(text):
    with pytest.raises(ConversionError):
        convert_layout(text)


def test_punctuation_and_case():
    assert convert_layout("Ghbdtn!") == "Привет!"
    assert convert_layout("ЙЦУКЕН") == "QWERTY"
    assert convert_layout("Привет!") == "Ghbdtn!"

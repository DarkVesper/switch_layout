import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from switch_layout.models import Translation
from switch_layout.services import (
    Statistics,
    format_stat,
    format_statistics,
    get_statistics,
    save_conversion,
)


def test_empty_database(session):
    assert get_statistics(session) == Statistics(0, 0, 0)
    assert format_statistics(session) == (
        "en-ru: 0 (0.0%)\nru-en: 0 (0.0%)\nСамый длинный текст: 0 символов"
    )


def test_stats_views_and_maximum(session):
    save_conversion(session, "en-ru", 6)
    save_conversion(session, "en-ru", 57)
    save_conversion(session, "ru-en", 7)

    assert get_statistics(session) == Statistics(2, 1, 57)
    assert format_statistics(session) == (
        "en-ru: 2 (66.7%)\nru-en: 1 (33.3%)\nСамый длинный текст: 57 символов"
    )
    assert format_statistics(session, "abs") == (
        "en-ru: 2\nru-en: 1\nСамый длинный текст: 57 символов"
    )
    assert format_statistics(session, "rel") == (
        "en-ru: 66.7%\nru-en: 33.3%\nСамый длинный текст: 57 символов"
    )


@pytest.mark.parametrize(
    ("count", "total", "view", "expected"),
    [
        (0, 0, None, "0 (0.0%)"),
        (0, 10, "rel", "0.0%"),
        (10, 10, "rel", "100.0%"),
        (1, 3, None, "1 (33.3%)"),
        (1, 3, "abs", "1"),
    ],
)
def test_format_stat(count, total, view, expected):
    assert format_stat(count, total, view) == expected


@pytest.mark.parametrize(
    ("count", "total", "view"),
    [(-1, 10, None), (11, 10, None), (1, -1, None), (1, 2, "other")],
)
def test_format_stat_invalid(count, total, view):
    with pytest.raises(ValueError):
        format_stat(count, total, view)


@pytest.mark.parametrize(
    ("direction", "length"),
    [("invalid", 3), ("en-ru", 0), ("en-ru", -5)],
)
def test_save_conversion_validation(session, direction, length):
    with pytest.raises(ValueError):
        save_conversion(session, direction, length)
    assert session.scalars(select(Translation)).all() == []


def test_database_rollback_on_constraint_violation(session):
    session.add(Translation(direction="invalid", length=3))
    with pytest.raises(IntegrityError):
        session.commit()
    session.rollback()

    save_conversion(session, "ru-en", 8)
    assert get_statistics(session) == Statistics(0, 1, 8)


def test_save_conversion_rolls_back_on_database_error(session, monkeypatch):
    rollback_calls = []
    real_rollback = session.rollback

    def fail_commit():
        raise IntegrityError("INSERT", {}, Exception("database error"))

    def track_rollback():
        rollback_calls.append(True)
        real_rollback()

    monkeypatch.setattr(session, "commit", fail_commit)
    monkeypatch.setattr(session, "rollback", track_rollback)

    with pytest.raises(IntegrityError):
        save_conversion(session, "en-ru", 10)

    assert rollback_calls == [True]
    assert not session.new

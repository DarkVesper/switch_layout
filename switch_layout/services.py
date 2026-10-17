"""Статистика конвертаций."""

from dataclasses import dataclass
from typing import Literal

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from switch_layout.layout import Direction
from switch_layout.models import Translation

View = Literal["abs", "rel"] | None


@dataclass(frozen=True)
class Statistics:
    en_ru: int
    ru_en: int
    longest: int

    @property
    def total(self) -> int:
        return self.en_ru + self.ru_en


def save_conversion(session: Session, direction: Direction, length: int) -> None:
    """Сохранить конвертацию; при ошибке откатить транзакцию."""
    if direction not in ("en-ru", "ru-en"):
        raise ValueError("Неизвестное направление конвертации.")
    if length <= 0:
        raise ValueError("Длина исходного текста должна быть положительной.")

    try:
        session.add(Translation(direction=direction, length=length))
        session.commit()
    except SQLAlchemyError:
        session.rollback()
        raise


def get_statistics(session: Session) -> Statistics:
    """Посчитать конвертации и найти максимальную длину текста."""
    rows = session.execute(
        select(Translation.direction, func.count(Translation.id)).group_by(
            Translation.direction
        )
    ).all()
    counts = dict(rows)
    longest = session.scalar(select(func.max(Translation.length))) or 0
    return Statistics(
        en_ru=counts.get("en-ru", 0),
        ru_en=counts.get("ru-en", 0),
        longest=longest,
    )


def format_stat(count: int, total: int, view: View = None) -> str:
    """Форматировать количество и долю конвертаций."""
    if view not in (None, "abs", "rel"):
        raise ValueError("Неизвестный формат статистики.")
    if count < 0 or total < 0 or count > total:
        raise ValueError("Некорректные значения статистики.")

    percent = count / total * 100 if total else 0
    if view == "abs":
        return f"{count}"
    if view == "rel":
        return f"{percent:.1f}%"
    return f"{count} ({percent:.1f}%)"


def format_statistics(session: Session, view: View = None) -> str:
    """Собрать сводку для команды stats."""
    data = get_statistics(session)
    return "\n".join(
        (
            f"en-ru: {format_stat(data.en_ru, data.total, view)}",
            f"ru-en: {format_stat(data.ru_en, data.total, view)}",
            f"Самый длинный текст: {data.longest} символов",
        )
    )

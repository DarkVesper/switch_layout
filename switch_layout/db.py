"""Подключение к базе статистики."""

from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from switch_layout.models import Base


@contextmanager
def get_session() -> Iterator[Session]:
    """Открыть stats.db и создать недостающие таблицы."""
    engine = create_engine("sqlite:///stats.db")
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            yield session
    finally:
        engine.dispose()

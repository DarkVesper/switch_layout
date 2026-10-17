from sqlalchemy import CheckConstraint, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Translation(Base):
    """Одна успешная конвертация раскладки."""

    __tablename__ = "translations"
    __table_args__ = (
        CheckConstraint("direction IN ('en-ru', 'ru-en')", name="valid_direction"),
        CheckConstraint("length > 0", name="positive_length"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    direction: Mapped[str] = mapped_column(String(5), nullable=False)
    length: Mapped[int] = mapped_column(Integer, nullable=False)

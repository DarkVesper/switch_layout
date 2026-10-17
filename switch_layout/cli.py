import logging

import click
import pyperclip
from sqlalchemy.exc import SQLAlchemyError

from switch_layout.db import get_session
from switch_layout.exceptions import ConversionError
from switch_layout.layout import convert_layout, detect_direction
from switch_layout.logging_config import configure_logging
from switch_layout.services import format_statistics, save_conversion

logger = logging.getLogger("switch_layout")


@click.group()
def cli() -> None:
    """Исправление ошибочной раскладки текста в буфере обмена."""
    try:
        configure_logging()
    except OSError as exc:
        raise click.ClickException(f"Не удалось создать app.log: {exc}") from exc


@cli.command()
def convert() -> None:
    """Конвертировать текст в буфере обмена и записать статистику."""
    try:
        original = pyperclip.paste()
        direction = detect_direction(original)
        result = convert_layout(original)
        pyperclip.copy(result)
    except ConversionError as exc:
        logger.warning("Конвертация отклонена: %s", exc)
        raise click.ClickException(str(exc)) from exc
    except (pyperclip.PyperclipException, OSError) as exc:
        logger.error("Ошибка работы с буфером: %s", exc)
        raise click.ClickException(
            f"Не удалось прочитать/записать буфер: {exc}"
        ) from exc

    try:
        with get_session() as session:
            save_conversion(session, direction, len(original))
    except SQLAlchemyError:
        logger.exception("Ошибка SQLite при записи конвертации")
        click.echo(
            "Предупреждение: текст преобразован и сохранён в буфер обмена, "
            "но статистика не записана из-за ошибки базы данных. "
            "Повторять команду не нужно. Подробности записаны в app.log.",
            err=True,
        )

    logger.info("Конвертация %s, длина %s", direction, len(original))
    click.echo(result)


@cli.command()
@click.option(
    "--view",
    type=click.Choice(["abs", "rel"]),
    default=None,
    help="abs — количество, rel — проценты; без опции — оба вида.",
)
def stats(view: str | None) -> None:
    """Показать число конвертаций и максимальную длину текста."""
    try:
        with get_session() as session:
            result = format_statistics(session, view)
    except SQLAlchemyError as exc:
        logger.exception("Ошибка SQLite при чтении статистики")
        raise click.ClickException(
            "Ошибка базы данных. Подробности записаны в app.log."
        ) from exc

    logger.info("Запрошена статистика (view=%s)", view or "both")
    click.echo(result)


if __name__ == "__main__":
    cli()

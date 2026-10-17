import logging


def configure_logging() -> None:
    """Настроить запись событий в app.log."""
    logger = logging.getLogger("switch_layout")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # При повторном запуске CLI не должны накапливаться обработчики.
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
        handler.close()

    handler = logging.FileHandler("app.log", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

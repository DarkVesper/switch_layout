import pyperclip
import pytest
from click.testing import CliRunner
from sqlalchemy.exc import OperationalError

import switch_layout.cli as cli_module


@pytest.fixture
def runner(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    yield CliRunner()

    # Закрываем app.log перед очисткой временной папки в Windows.
    for handler in cli_module.logger.handlers[:]:
        cli_module.logger.removeHandler(handler)
        handler.close()


def test_convert_then_stats(monkeypatch, runner):
    clipboard = {"value": "ghbdtn"}
    monkeypatch.setattr(pyperclip, "paste", lambda: clipboard["value"])
    monkeypatch.setattr(pyperclip, "copy", lambda value: clipboard.update(value=value))

    convert = runner.invoke(cli_module.cli, ["convert"])
    assert convert.exit_code == 0, convert.output
    assert "привет" in convert.output
    assert clipboard["value"] == "привет"

    stats = runner.invoke(cli_module.cli, ["stats"])
    assert stats.exit_code == 0, stats.output
    assert "en-ru: 1 (100.0%)" in stats.output
    assert "ru-en: 0 (0.0%)" in stats.output
    assert "Самый длинный текст: 6 символов" in stats.output

    with open("app.log", encoding="utf-8") as log_file:
        log = log_file.read()
    assert "Конвертация en-ru" in log
    assert "Запрошена статистика" in log


def test_stats_empty_and_invalid_choice(runner):
    empty = runner.invoke(cli_module.cli, ["stats", "--view", "rel"])
    assert empty.exit_code == 0
    assert "en-ru: 0.0%" in empty.output
    assert "Самый длинный текст: 0 символов" in empty.output

    invalid = runner.invoke(cli_module.cli, ["stats", "--view", "wrong"])
    assert invalid.exit_code != 0
    assert "Invalid value" in invalid.output


def test_empty_clipboard_returns_failure(monkeypatch, runner):
    monkeypatch.setattr(pyperclip, "paste", lambda: "")
    result = runner.invoke(cli_module.cli, ["convert"])
    assert result.exit_code != 0
    assert "Буфер обмена пуст" in result.output


def test_clipboard_backend_error(monkeypatch, runner):
    def fail():
        raise pyperclip.PyperclipException("clipboard недоступен")

    monkeypatch.setattr(pyperclip, "paste", fail)
    result = runner.invoke(cli_module.cli, ["convert"])
    assert result.exit_code != 0
    assert "Не удалось прочитать/записать буфер" in result.output


def test_database_error_returns_failure(monkeypatch, runner):
    def fail():
        raise OperationalError("SELECT", {}, Exception("disk error"))

    monkeypatch.setattr(cli_module, "get_session", fail)
    result = runner.invoke(cli_module.cli, ["stats"])
    assert result.exit_code != 0
    assert "Ошибка базы данных" in result.output
    with open("app.log", encoding="utf-8") as log_file:
        assert "disk error" in log_file.read()


@pytest.mark.parametrize("failure_stage", ["get_session", "save_conversion"])
def test_database_failure_after_copy_reports_success(
    monkeypatch, failure_stage, runner
):
    clipboard = {"value": "ghbdtn"}
    monkeypatch.setattr(pyperclip, "paste", lambda: clipboard["value"])
    monkeypatch.setattr(pyperclip, "copy", lambda value: clipboard.update(value=value))

    def fail(*args):
        raise OperationalError("INSERT", {}, Exception("disk error"))

    monkeypatch.setattr(cli_module, failure_stage, fail)
    result = runner.invoke(cli_module.cli, ["convert"])
    assert result.exit_code == 0, result.output
    assert result.output.endswith("привет\n")
    assert clipboard["value"] == "привет"
    assert "статистика не записана" in result.output
    assert "Повторять команду не нужно" in result.output
    with open("app.log", encoding="utf-8") as log_file:
        assert "disk error" in log_file.read()


def test_copy_error_does_not_save_a_conversion(monkeypatch, runner):
    monkeypatch.setattr(pyperclip, "paste", lambda: "ghbdtn")

    def fail_copy(_text):
        raise pyperclip.PyperclipException("clipboard locked")

    monkeypatch.setattr(pyperclip, "copy", fail_copy)
    failed = runner.invoke(cli_module.cli, ["convert"])
    assert failed.exit_code != 0
    assert "Не удалось прочитать/записать буфер" in failed.output

    stats = runner.invoke(cli_module.cli, ["stats", "--view", "abs"])
    assert stats.exit_code == 0
    assert "en-ru: 0" in stats.output

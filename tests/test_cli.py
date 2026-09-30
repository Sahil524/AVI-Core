from __future__ import annotations

from click.testing import CliRunner

from app import cli


def test_cli_version():
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "avicore v2.0.0" in result.output


def test_cli_help_flag():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Show this message and exit." in result.output
    assert "menu" in result.output
    assert "video" in result.output
    assert "audio" in result.output
    assert "image" in result.output


def test_cli_help_command():
    runner = CliRunner()
    result = runner.invoke(cli, ["help"])
    assert result.exit_code == 0
    assert "AVI CORE" in result.output
    assert "avicore menu install" in result.output


def test_cli_menu_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["menu", "--help"])
    assert result.exit_code == 0
    assert "install" in result.output
    assert "remove" in result.output

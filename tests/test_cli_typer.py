from typer.testing import CliRunner

from laya_find.cli import app

runner = CliRunner()


def test_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "url" in result.stdout.lower() or "URL" in result.stdout
    assert "COMMAND [ARGS]" not in result.stdout


def test_missing_required_exits_two():
    result = runner.invoke(app, ["--json"])
    assert result.exit_code == 2

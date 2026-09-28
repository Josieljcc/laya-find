from typer.testing import CliRunner

from laya_find.login_cli import app
from laya_find.login_flow import LoginWizardOptions, run_wizard


runner = CliRunner()


def test_login_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "login" in result.stdout.lower() or "Login" in result.stdout


def test_wizard_without_login_url_and_no_tty_exits_two(monkeypatch):
    monkeypatch.setattr("sys.stdin.isatty", lambda: False)
    code = run_wizard(LoginWizardOptions(login_url=""))
    assert code == 2

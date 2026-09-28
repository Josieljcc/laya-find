"""CLI entry for ``laya-login``: manual login then find on the same session."""

from __future__ import annotations

import os

import typer

from laya_find.find import (
    DEFAULT_BATCH,
    DEFAULT_CACHE_PATH,
    DEFAULT_SERVE,
)
from laya_find.login_flow import LoginWizardOptions, run_wizard

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Login manual (headed) e depois laya-find na mesma sessão Playwright",
)


@app.command()
def _entrypoint(
    login_url: str = typer.Option("", "--login-url", help="Página onde você autentica"),
    url: str = typer.Option("", "--url", envvar="LAYA_FIND_URL"),
    intent: str = typer.Option("", "--intent"),
    mode: str = typer.Option("dom", "--mode", help="dom|network|both"),
    kind: str = typer.Option(
        "", "--kind", help="input|button|link|select|network|clickable|image"
    ),
    serve: str = typer.Option(
        os.environ.get("LAYA_SERVE_URL", DEFAULT_SERVE), "--serve"
    ),
    settle_ms: int = typer.Option(1500, "--settle-ms"),
    timeout_ms: int = typer.Option(30000, "--timeout-ms"),
    batch_size: int = typer.Option(DEFAULT_BATCH, "--batch-size"),
    policy: str = typer.Option("light", "--policy", help="none|light|strict"),
    no_tournament: bool = typer.Option(False, "--no-tournament"),
    no_confirm: bool = typer.Option(False, "--no-confirm"),
    reveal: bool = typer.Option(False, "--reveal"),
    use_cache: bool = typer.Option(True, "--use-cache/--no-cache"),
    cache_path: str = typer.Option(DEFAULT_CACHE_PATH, "--cache-path"),
    json_out: bool = typer.Option(False, "--json", help="stdout: one JSON line"),
    loop: bool = typer.Option(
        False, "--loop", help="Perguntar outro intent na mesma sessão"
    ),
) -> None:
    if mode and mode not in ("dom", "network", "both"):
        raise typer.BadParameter("mode must be dom|network|both")
    if kind and kind not in (
        "input",
        "button",
        "link",
        "select",
        "network",
        "clickable",
        "image",
    ):
        raise typer.BadParameter("invalid kind")
    if policy not in ("none", "light", "strict"):
        raise typer.BadParameter("policy must be none|light|strict")

    code = run_wizard(
        LoginWizardOptions(
            login_url=login_url,
            url=url,
            intent=intent,
            mode=mode,
            kind=kind,
            serve=serve,
            settle_ms=settle_ms,
            timeout_ms=timeout_ms,
            batch_size=batch_size,
            policy=policy,
            no_tournament=no_tournament,
            no_confirm=no_confirm,
            reveal=reveal,
            use_cache=use_cache,
            cache_path=cache_path,
            json_stdout=json_out,
            loop=loop,
        )
    )
    raise typer.Exit(code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

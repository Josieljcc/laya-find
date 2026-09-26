from __future__ import annotations

import os

import typer

from laya_find.find import (
    DEFAULT_BATCH,
    DEFAULT_CACHE_PATH,
    DEFAULT_SERVE,
    FindOptions,
    run,
)

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Encontrar componente/request com Playwright + Laya",
)


@app.callback(invoke_without_command=True)
def _entrypoint(
    ctx: typer.Context,
    url: str = typer.Option("", "--url", envvar="LAYA_FIND_URL"),
    intent: str = typer.Option("", "--intent"),
    mode: str = typer.Option("", "--mode", help="dom|network|both"),
    kind: str = typer.Option(
        "", "--kind", help="input|button|link|select|network"
    ),
    serve: str = typer.Option(
        os.environ.get("LAYA_SERVE_URL", DEFAULT_SERVE), "--serve"
    ),
    headed: bool = typer.Option(False, "--headed"),
    listen_seconds: float = typer.Option(5.0, "--listen-seconds"),
    settle_ms: int = typer.Option(1500, "--settle-ms"),
    timeout_ms: int = typer.Option(30000, "--timeout-ms"),
    batch_size: int = typer.Option(DEFAULT_BATCH, "--batch-size"),
    policy: str = typer.Option(
        "light", "--policy", help="none|light|strict"
    ),
    no_tournament: bool = typer.Option(False, "--no-tournament"),
    no_confirm: bool = typer.Option(False, "--no-confirm"),
    reveal: bool = typer.Option(False, "--reveal"),
    use_cache: bool = typer.Option(True, "--use-cache/--no-cache"),
    cache_path: str = typer.Option(DEFAULT_CACHE_PATH, "--cache-path"),
    json_out: bool = typer.Option(
        False, "--json", help="stdout: one JSON line"
    ),
) -> None:
    if ctx.invoked_subcommand is not None:
        return
    if mode and mode not in ("dom", "network", "both"):
        raise typer.BadParameter("mode must be dom|network|both")
    if kind and kind not in ("input", "button", "link", "select", "network"):
        raise typer.BadParameter("invalid kind")
    if policy not in ("none", "light", "strict"):
        raise typer.BadParameter("policy must be none|light|strict")

    code = run(
        FindOptions(
            url=url,
            intent=intent,
            mode=mode,
            kind=kind,
            serve=serve,
            headed=headed,
            listen_seconds=listen_seconds,
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
        )
    )
    raise typer.Exit(code)


def main() -> None:
    app()


if __name__ == "__main__":
    main()

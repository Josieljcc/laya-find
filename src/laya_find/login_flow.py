"""Interactive headed login then find on the same Playwright page."""

from __future__ import annotations

import sys
from dataclasses import dataclass

from playwright.sync_api import sync_playwright

from laya_find.find import DEFAULT_SERVE, FindOptions, run_on_page


@dataclass
class LoginWizardOptions:
    login_url: str = ""
    url: str = ""
    intent: str = ""
    mode: str = "dom"
    kind: str = ""
    serve: str = DEFAULT_SERVE
    settle_ms: int = 1500
    timeout_ms: int = 30000
    batch_size: int = 10
    policy: str = "light"
    no_tournament: bool = False
    no_confirm: bool = False
    reveal: bool = False
    use_cache: bool = True
    cache_path: str = "selector_cache.json"
    json_stdout: bool = False
    loop: bool = False


def _prompt(label: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    raw = input(f"{label}{suffix}: ").strip()
    return raw or default


def _ensure_tty() -> bool:
    if sys.stdin.isatty():
        return True
    print(
        "laya-login precisa de terminal interativo (ou passe --login-url/--url/--intent).",
        file=sys.stderr,
    )
    return False


def _build_find_options(wiz: LoginWizardOptions, url: str, intent: str, mode: str) -> FindOptions:
    return FindOptions(
        url=url,
        intent=intent,
        mode=mode,
        kind=wiz.kind,
        serve=wiz.serve,
        headed=True,
        settle_ms=wiz.settle_ms,
        timeout_ms=wiz.timeout_ms,
        batch_size=wiz.batch_size,
        policy=wiz.policy,
        no_tournament=wiz.no_tournament,
        no_confirm=wiz.no_confirm,
        reveal=wiz.reveal,
        use_cache=wiz.use_cache,
        cache_path=wiz.cache_path,
        json_stdout=wiz.json_stdout,
    )


def run_wizard(wiz: LoginWizardOptions) -> int:
    """Open headed Chromium, wait for manual login, then run find on same page."""
    login_url = wiz.login_url
    if not login_url:
        if not _ensure_tty():
            return 2
        login_url = _prompt("URL de login")
    if not login_url:
        print("URL de login é obrigatória.", file=sys.stderr)
        return 2

    last_code = 2
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        page.set_default_timeout(wiz.timeout_ms)
        try:
            print(f"Abrindo {login_url}")
            page.goto(login_url, wait_until="domcontentloaded")
            print("Faça o login na janela do Chromium.")
            if sys.stdin.isatty():
                input("Quando terminar, volte aqui e pressione Enter…")
            else:
                print(
                    "stdin não é TTY — não dá para esperar Enter. Abortando.",
                    file=sys.stderr,
                )
                return 2

            while True:
                url = wiz.url
                intent = wiz.intent
                mode = wiz.mode or "dom"
                if (not url or not intent) and not _ensure_tty():
                    return 2
                if not url:
                    url = _prompt("URL da página para buscar")
                if not intent:
                    intent = _prompt("Intent (o que encontrar)")
                if not mode:
                    mode = _prompt("Modo (dom|network|both)", "dom")
                if mode not in ("dom", "network", "both"):
                    print("mode inválido; usando dom.", file=sys.stderr)
                    mode = "dom"
                if not url or not intent:
                    print("URL e intent são obrigatórios.", file=sys.stderr)
                    last_code = 2
                    break

                opts = _build_find_options(wiz, url, intent, mode)
                last_code = run_on_page(page, opts)

                if not wiz.loop:
                    break
                if not sys.stdin.isatty():
                    break
                again = _prompt("Outro find nesta sessão? (s/N)", "N").lower()
                if again not in ("s", "sim", "y", "yes"):
                    break
                # Clear one-shot flags so prompts ask again
                wiz.url = ""
                wiz.intent = ""
        finally:
            browser.close()
    return last_code

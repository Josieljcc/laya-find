"""Login manual headed + salva storage_state (demo mínimo).

Preferido para login + find na mesma sessão:
  .\\.venv\\Scripts\\laya-login.exe --login-url "https://SEU_SITE/login"

Uso deste script (só gravar auth.json):
  .\\.venv\\Scripts\\python.exe examples\\save_auth.py --url "https://SEU_SITE/login"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def main() -> None:
    p = argparse.ArgumentParser(description="Login manual e salva auth.json")
    p.add_argument("--url", required=True, help="URL da página de login")
    p.add_argument(
        "--out",
        default="auth.json",
        help="Arquivo de storage_state (padrão: ./auth.json)",
    )
    args = p.parse_args()
    out = Path(args.out)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(args.url, wait_until="domcontentloaded")
        print("Faça o login na janela do Chromium.")
        print("Quando terminar, volte aqui e pressione Enter…")
        input()
        context.storage_state(path=str(out))
        print(f"Sessão salva em {out.resolve()}")
        browser.close()


if __name__ == "__main__":
    main()

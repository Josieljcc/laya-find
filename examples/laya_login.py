"""Login assistido por Laya (experimental).

Playwright lê a página, Laya escolhe user/senha/submit e opcionalmente preenche.

Para **só descobrir seletores** (contrato scraper / --json), use em vez disso:
  laya-find (.\.venv\Scripts\laya-find.exe)
  examples/LAYA_FIND.md
  examples/README.md

Este script ainda faz fill+click — fora do escopo do find atual.

Requer:
  - laya-serve em http://127.0.0.1:8000  (ou LAYA_SERVE_URL)
  - playwright + chromium no .venv
  - LAYA_LOGIN_USER / LAYA_LOGIN_PASS no ambiente (nunca no código)

Uso:
  $env:LAYA_LOGIN_USER='seu_usuario'
  $env:LAYA_LOGIN_PASS='sua_senha'
  .\\.venv\\Scripts\\python.exe examples\\laya_login.py --discover-only
  .\\.venv\\Scripts\\python.exe examples\\laya_login.py --headed

Flags:
  --discover-only   só lista campos e decisão do Laya (não preenche)
  --headed          abre o browser visível
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass

from playwright.sync_api import sync_playwright

DEFAULT_URL = "https://luiscorreia.servidorcaju.com.br/login"
DEFAULT_SERVE = "http://127.0.0.1:8000"


@dataclass
class Field:
    key: str
    kind: str  # input | button | link
    selector: str
    summary: str


def _reconfigure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def extract_fields(page) -> list[Field]:
    """Collect usable login controls from the live DOM."""
    raw = page.evaluate(
        """() => {
          const out = [];
          const push = (el, kind, extra) => {
            const tag = el.tagName.toLowerCase();
            const type = (el.getAttribute('type') || '').toLowerCase();
            if (kind === 'input' && ['hidden', 'submit', 'button', 'checkbox', 'radio', 'file'].includes(type)) {
              // submit/button inputs still useful as submit candidates
              if (!['submit', 'button'].includes(type) && type !== '') return;
              if (type === 'hidden' || type === 'checkbox' || type === 'radio' || type === 'file') return;
            }
            const id = el.id || '';
            const name = el.getAttribute('name') || '';
            const placeholder = el.getAttribute('placeholder') || '';
            const aria = el.getAttribute('aria-label') || '';
            const text = (el.innerText || el.value || '').trim().slice(0, 80);
            let label = '';
            if (id) {
              const lab = document.querySelector(`label[for="${CSS.escape(id)}"]`);
              if (lab) label = (lab.innerText || '').trim().slice(0, 80);
            }
            if (!label) {
              const parentLab = el.closest('label');
              if (parentLab) label = (parentLab.innerText || '').trim().slice(0, 80);
            }
            let selector = '';
            if (id) selector = `#${CSS.escape(id)}`;
            else if (name) selector = `${tag}[name="${name.replace(/"/g, '\\\\"')}"]`;
            else if (aria) selector = `${tag}[aria-label="${aria.replace(/"/g, '\\\\"')}"]`;
            else if (placeholder) selector = `${tag}[placeholder="${placeholder.replace(/"/g, '\\\\"')}"]`;
            else selector = tag;
            out.push({
              kind,
              tag,
              type,
              id,
              name,
              placeholder,
              aria,
              label,
              text,
              selector,
              ...extra,
            });
          };

          document.querySelectorAll('input:not([type="hidden"])').forEach(el => {
            const type = (el.getAttribute('type') || 'text').toLowerCase();
            if (['checkbox', 'radio', 'file', 'image', 'reset', 'color', 'range'].includes(type)) return;
            push(el, 'input', {});
          });
          document.querySelectorAll('textarea').forEach(el => push(el, 'input', {}));
          document.querySelectorAll('button, input[type="submit"], input[type="button"]').forEach(el => {
            const type = (el.getAttribute('type') || '').toLowerCase();
            const id = el.id || '';
            const text = (el.innerText || el.value || '').trim();
            const aria = el.getAttribute('aria-label') || '';
            // Skip decorative / empty chrome (chat widgets, icon toggles without label)
            if (type !== 'submit' && !id && !text && !aria) return;
            push(el, 'button', {});
          });
          document.querySelectorAll('a[href]').forEach(el => {
            const t = (el.innerText || '').trim().toLowerCase();
            if (!t) return;
            if (/(entrar|login|acessar|sign in|submit|enviar)/i.test(t)) push(el, 'link', {});
          });
          return out;
        }"""
    )

    fields: list[Field] = []
    for i, item in enumerate(raw, 1):
        key = f"field_{i}"
        bits = [
            f"kind={item['kind']}",
            f"tag={item['tag']}",
        ]
        if item.get("type"):
            bits.append(f"type={item['type']}")
        if item.get("name"):
            bits.append(f"name={item['name']}")
        if item.get("id"):
            bits.append(f"id={item['id']}")
        if item.get("placeholder"):
            bits.append(f"placeholder={item['placeholder']}")
        if item.get("label"):
            bits.append(f"label={item['label']}")
        if item.get("aria"):
            bits.append(f"aria-label={item['aria']}")
        if item.get("text"):
            bits.append(f"text={item['text']}")
        summary = f"{key}: " + ", ".join(bits)
        fields.append(Field(key=key, kind=item["kind"], selector=item["selector"], summary=summary))
    return fields


def fields_state(fields: list[Field], page_url: str, title: str) -> str:
    lines = [
        f"Login page URL: {page_url}",
        f"Page title: {title}",
        "Candidate controls on the page:",
        *[f.summary for f in fields],
    ]
    return "\n".join(lines)


def _criteria(fields: list[Field], pred) -> dict[str, str]:
    picked = {f.key: f.summary for f in fields if pred(f)}
    return picked


def laya_pick_fields(state: str, fields: list[Field], serve_url: str) -> tuple[dict, float]:
    all_criteria = {f.key: f.summary for f in fields}
    if len(all_criteria) < 2:
        raise RuntimeError("Página não expôs controles suficientes para o Laya decidir.")

    # Narrow each question to plausible candidates so choice options stay distinct.
    user_crit = _criteria(
        fields,
        lambda f: f.kind == "input"
        and "type=password" not in f.summary
        and "type=submit" not in f.summary,
    ) or all_criteria
    pass_crit = _criteria(
        fields,
        lambda f: f.kind == "input" and "type=password" in f.summary,
    ) or _criteria(fields, lambda f: f.kind == "input") or all_criteria
    submit_crit = _criteria(
        fields,
        lambda f: (
            "type=submit" in f.summary
            or "btn-login" in f.summary.lower()
            or any(
                w in f.summary.lower()
                for w in ("entrar", "login", "acessar", "sign in", "enviar")
            )
        ),
    ) or _criteria(fields, lambda f: f.kind in ("button", "link")) or all_criteria

    questions = {
        "username_field": {
            "type": "choice",
            "instructions": (
                "Which control is the username / email / login input "
                "(not password, not submit)?"
            ),
            "criteria": user_crit,
        },
        "password_field": {
            "type": "choice",
            "instructions": "Which control is the password input (type=password)?",
            "criteria": pass_crit,
        },
        "submit_control": {
            "type": "choice",
            "instructions": (
                "Which control submits the login form "
                "(button Entrar/Login/Acessar or type=submit)?"
            ),
            "criteria": submit_crit,
        },
    }

    payload = json.dumps(
        {
            "state": {"body": state},
            "questions": questions,
            "model": "multilingual",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{serve_url.rstrip('/')}/v1/systemone",
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    ms = (time.perf_counter() - t0) * 1000
    return body, ms


def by_key(fields: list[Field], key: str) -> Field:
    for f in fields:
        if f.key == key:
            return f
    raise KeyError(key)


def main() -> int:
    _reconfigure_stdout()
    parser = argparse.ArgumentParser(description="Login com Playwright + Laya")
    parser.add_argument("--url", default=os.environ.get("LAYA_LOGIN_URL", DEFAULT_URL))
    parser.add_argument("--serve", default=os.environ.get("LAYA_SERVE_URL", DEFAULT_SERVE))
    parser.add_argument("--discover-only", action="store_true")
    parser.add_argument("--headed", action="store_true")
    parser.add_argument("--timeout-ms", type=int, default=30000)
    args = parser.parse_args()

    user = os.environ.get("LAYA_LOGIN_USER", "").strip()
    password = os.environ.get("LAYA_LOGIN_PASS", "")
    if not args.discover_only and (not user or password == ""):
        print(
            "Defina LAYA_LOGIN_USER e LAYA_LOGIN_PASS, ou use --discover-only.",
            file=sys.stderr,
        )
        return 2

    try:
        with urllib.request.urlopen(f"{args.serve.rstrip('/')}/health", timeout=5) as resp:
            health = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        print(f"laya-serve offline em {args.serve}: {exc}", file=sys.stderr)
        return 1

    print(f"laya-serve ok · loaded={health.get('loaded')} · device={health.get('device')}")
    print(f"abrindo {args.url}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headed)
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout(args.timeout_ms)
        page.goto(args.url, wait_until="domcontentloaded")
        page.wait_for_timeout(800)  # deixa JS montar o formulário

        fields = extract_fields(page)
        if not fields:
            print("Nenhum campo utilizável encontrado no DOM.", file=sys.stderr)
            # dump short HTML hint
            print(page.content()[:500], file=sys.stderr)
            browser.close()
            return 1

        print("-" * 72)
        print("Campos encontrados:")
        for f in fields:
            print(f"  {f.summary}")
        print("-" * 72)

        state = fields_state(fields, page.url, page.title())
        result, ms = laya_pick_fields(state, fields, args.serve)
        answers = result["answers"]
        user_key = answers["username_field"]["choice"]
        pass_key = answers["password_field"]["choice"]
        submit_key = answers["submit_control"]["choice"]

        user_f = by_key(fields, user_key)
        pass_f = by_key(fields, pass_key)
        submit_f = by_key(fields, submit_key)

        print(f"Laya ({ms:.1f} ms) · route={result.get('routing', {}).get('model')}")
        print(f"  username -> {user_f.key}  ({user_f.selector})")
        print(f"  password -> {pass_f.key}  ({pass_f.selector})")
        print(f"  submit   -> {submit_f.key} ({submit_f.selector})")

        if args.discover_only:
            print("\n--discover-only: não preenchi o formulário.")
            browser.close()
            return 0

        page.fill(user_f.selector, user)
        page.fill(pass_f.selector, password)
        before = page.url
        page.click(submit_f.selector)
        try:
            page.wait_for_load_state("networkidle", timeout=args.timeout_ms)
        except Exception:
            page.wait_for_timeout(2000)

        after = page.url
        print("-" * 72)
        print(f"URL antes : {before}")
        print(f"URL depois: {after}")
        if after.rstrip("/") != before.rstrip("/"):
            print("Login parece ter navegado para outra página.")
        else:
            print(
                "URL não mudou — confira credenciais, captcha ou mensagem de erro na tela."
            )
        browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

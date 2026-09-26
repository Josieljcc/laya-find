# Market CLI Packaging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Empacotar o descobridor como CLI instalável (`pip install -e .` → `laya-find` / `python -m laya_find`) com layout `src/`, Typer, e demos só em `examples/`.

**Architecture:** Mover `examples/laya_find_lib/*` e a orquestração de `examples/laya_find.py` para `src/laya_find/`; Typer em `cli.py` chama `find.run(FindOptions)`; entry points via `pyproject.toml` (hatchling). Comportamento de descoberta e contrato JSON permanecem; removem-se `--action` e `--interactive`.

**Tech Stack:** Python ≥3.10, hatchling, Typer, Playwright, laya[serve], pytest.

**Spec:** [docs/superpowers/specs/2026-09-26-market-cli-packaging-design.md](../specs/2026-09-26-market-cli-packaging-design.md)

## Global Constraints

- `requires-python = ">=3.10"`
- Dependencies runtime: `laya[serve]`, `playwright`, `typer`
- Dev optional: `pytest`, `ruff`
- Entry: `laya-find = "laya_find.cli:main"`; também `python -m laya_find`
- Cache default: `./selector_cache.json` (cwd), não `examples/selector_cache.json`
- `--json`: uma linha JSON em stdout; logs em stderr
- Exit codes: `0` ok, `1` descoberta falhou, `2` uso/config
- Remover da CLI: `--action`, `--interactive`
- Sem publicar PyPI; sem multi-comando; sem mudar políticas/torneio/JSON fields
- Commits: só se o humano pedir e existir `.git` (este workspace pode não ter git — pule passos de commit)
- PowerShell: preferir `.\.venv\Scripts\...`

## File map

| Path | Responsibility |
|------|----------------|
| `pyproject.toml` | Packaging, scripts, deps |
| `src/laya_find/__init__.py` | `__version__` |
| `src/laya_find/__main__.py` | `python -m laya_find` |
| `src/laya_find/cli.py` | Typer flags → `FindOptions` → exit |
| `src/laya_find/find.py` | Pipeline (ex-`laya_find.py` sem argparse legado) |
| `src/laya_find/{selectors,policy,normalize,decide,cache,contract}.py` | Lib (ex-`laya_find_lib`) |
| `tests/*` | Imports `laya_find.*` + CliRunner |
| `examples/*.ps1`, docs | Chamam `laya-find` |
| Delete | `examples/laya_find.py`, `laya_find_lib/`, `laya_find_heuristic.py`, `examples/__init__.py` |

---

### Task 1: Packaging scaffold (`pyproject.toml` + stub package)

**Files:**
- Create: `pyproject.toml`
- Create: `src/laya_find/__init__.py`
- Modify: `.gitignore`
- Modify: `pytest.ini`
- Test: `tests/test_package_meta.py` (novo, temporário até Task 2 consolidar)

**Interfaces:**
- Produces: package name `laya_find`, `__version__ = "0.1.0"`, editable install works

- [ ] **Step 1: Write failing meta test**

Create `tests/test_package_meta.py`:

```python
def test_version_importable():
    import laya_find

    assert laya_find.__version__ == "0.1.0"
```

- [ ] **Step 2: Run test — expect fail**

```powershell
Set-Location C:\laya
.\.venv\Scripts\python.exe -m pytest tests\test_package_meta.py -q
```

Expected: `ModuleNotFoundError: No module named 'laya_find'` (or collection error).

- [ ] **Step 3: Add `pyproject.toml`**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "laya-find"
version = "0.1.0"
description = "Discover stable DOM/network selectors with Playwright + Laya"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
  "laya[serve]",
  "playwright",
  "typer",
]

[project.optional-dependencies]
dev = [
  "pytest>=8",
  "ruff",
]

[project.scripts]
laya-find = "laya_find.cli:main"

[tool.hatch.build.targets.wheel]
packages = ["src/laya_find"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 4: Stub package + gitignore + pytest.ini**

`src/laya_find/__init__.py`:

```python
"""Discover stable selectors for an external scraper (Playwright + Laya)."""

__version__ = "0.1.0"
```

Append to `.gitignore`:

```
dist/
build/
*.egg-info/
.ruff_cache/
selector_cache.json
```

Replace `pytest.ini` with (hatch/pytest config also in pyproject; keep file minimal for clarity):

```ini
[pytest]
testpaths = tests
```

Remove `pythonpath = .` (editable install replaces it).

- [ ] **Step 5: Install editable + pass meta test**

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests\test_package_meta.py -q
```

Expected: `1 passed`.

Also create a placeholder so entry point import does not break later tasks — temporary `src/laya_find/cli.py`:

```python
def main() -> None:
    raise SystemExit("cli not implemented yet")
```

- [ ] **Step 6: Commit (only if user asked + git exists)**

```powershell
git add pyproject.toml src/laya_find/.gitignore pytest.ini tests/test_package_meta.py
# fix: add .gitignore not under src
git add .gitignore
git commit -m "build: add pyproject and src/laya_find package scaffold"
```

---

### Task 2: Move library modules + retarget unit tests

**Files:**
- Create: `src/laya_find/selectors.py` (copy from `examples/laya_find_lib/selectors.py`)
- Create: `src/laya_find/policy.py`, `normalize.py`, `decide.py`, `cache.py`, `contract.py` (same)
- Modify: all `tests/test_*.py` that import `examples.laya_find_lib.*`
- Do **not** delete `examples/laya_find_lib` yet (CLI ainda depende até Task 4–5)

**Interfaces:**
- Produces: `from laya_find.selectors import ...` etc. (API pública idêntica aos módulos atuais)

- [ ] **Step 1: Update one test import (TDD anchor)**

In `tests/test_selectors.py`, change:

```python
from laya_find.selectors import (
```

(keeping the rest of the import list identical). Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_selectors.py -q
```

Expected: FAIL `ModuleNotFoundError` or `ImportError` until copy exists.

- [ ] **Step 2: Copy lib modules into `src/laya_find/`**

```powershell
Copy-Item C:\laya\examples\laya_find_lib\selectors.py C:\laya\src\laya_find\selectors.py
Copy-Item C:\laya\examples\laya_find_lib\policy.py C:\laya\src\laya_find\policy.py
Copy-Item C:\laya\examples\laya_find_lib\normalize.py C:\laya\src\laya_find\normalize.py
Copy-Item C:\laya\examples\laya_find_lib\decide.py C:\laya\src\laya_find\decide.py
Copy-Item C:\laya\examples\laya_find_lib\cache.py C:\laya\src\laya_find\cache.py
Copy-Item C:\laya\examples\laya_find_lib\contract.py C:\laya\src\laya_find\contract.py
```

If any module had relative imports to siblings, keep them as `from laya_find.X import` or relative `.X` — mirror existing style (today they are mostly self-contained).

- [ ] **Step 3: Retarget all unit test imports**

Replace `from examples.laya_find_lib.` → `from laya_find.` in:

- `tests/test_selectors.py`
- `tests/test_policy.py`
- `tests/test_normalize.py`
- `tests/test_decide.py` / `test_tournament_labels.py`
- `tests/test_cache.py`
- `tests/test_result_contract.py`

- [ ] **Step 4: Run lib unit tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_selectors.py tests\test_policy.py tests\test_normalize.py tests\test_tournament_labels.py tests\test_cache.py tests\test_result_contract.py -q
```

Expected: all pass. (`test_cli_behavior.py` still imports `examples.laya_find` — leave for Task 4.)

- [ ] **Step 5: Commit (optional)**

```powershell
git add src/laya_find/*.py tests/
git commit -m "refactor: move laya_find_lib modules into src/laya_find"
```

---

### Task 3: Port orchestration to `find.py` + `FindOptions`

**Files:**
- Create: `src/laya_find/find.py` (from `examples/laya_find.py`)
- Test: extend `tests/test_cli_behavior.py` to import `laya_find.find`

**Interfaces:**
- Produces:
  - `@dataclass FindOptions` with fields matching preserved flags
  - `def run(options: FindOptions) -> int`
  - Keep: `settle_page`, `cache_lookup_allowed`, `Candidate`, helpers used by tests
- Consumes: `laya_find.{contract,cache,decide,normalize,policy,selectors}`

- [ ] **Step 1: Write failing tests against new module surface**

Replace top of `tests/test_cli_behavior.py` imports and parsing checks:

```python
import json

from laya_find.find import FindOptions, cache_lookup_allowed, run, settle_page


class SettlePage:
    def __init__(self):
        self.password_queries = 0
        self.clicks = 0

    def wait_for_load_state(self, *_args, **_kwargs):
        return None

    def wait_for_timeout(self, _timeout):
        return None

    def query_selector_all(self, _selector):
        self.password_queries += 1
        return []

    def locator(self, _selector):
        self.clicks += 1
        raise AssertionError("default discovery must not attempt reveal")


def test_reveal_default_false_and_settle_never_clicks():
    opts = FindOptions(
        url="https://example.com",
        intent="x",
        mode="dom",
        reveal=False,
    )
    page = SettlePage()
    settle_page(page, 300, "input", reveal=opts.reveal)
    assert opts.reveal is False
    assert page.password_queries == 0
    assert page.clicks == 0


def test_dom_cache_lookup_is_disabled_for_network_discovery():
    assert cache_lookup_allowed("dom", "input") is True
    assert cache_lookup_allowed("both", "link") is True
    assert cache_lookup_allowed("network", "input") is False
    assert cache_lookup_allowed("both", "network") is False
    assert cache_lookup_allowed("dom", "network") is False


def test_json_runtime_failure_emits_one_object_and_nonzero(monkeypatch, capsys):
    def fail(_options):
        raise RuntimeError("navigation exploded")

    monkeypatch.setattr("laya_find.find._run_impl", fail)

    exit_code = run(
        FindOptions(
            url="https://example.com",
            mode="dom",
            intent="login",
            json_stdout=True,
        )
    )

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert exit_code != 0
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["ok"] is False
    assert result["text"] == "navigation exploded"
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cli_behavior.py -q
```

Expected: FAIL (no `laya_find.find`).

- [ ] **Step 2: Copy and adapt `find.py`**

```powershell
Copy-Item C:\laya\examples\laya_find.py C:\laya\src\laya_find\find.py
```

Then edit `src/laya_find/find.py`:

1. Remove `sys.path` hack and `argparse` imports usage for public API.
2. Change imports:

```python
from laya_find.contract import build_result, emit_json_line, summary_field
from laya_find.cache import CacheStore, cache_key
from laya_find.decide import candidates_overlapping_intent, short_label
from laya_find.normalize import dedupe_by_destination
from laya_find.policy import apply_policy
from laya_find.selectors import is_volatile_selector, stable_href_candidates
```

3. Change default cache path:

```python
DEFAULT_CACHE_PATH = "selector_cache.json"  # cwd-relative
```

4. Add dataclass (near top, after constants):

```python
@dataclass
class FindOptions:
    url: str = ""
    intent: str = ""
    mode: str = ""
    kind: str = ""
    serve: str = DEFAULT_SERVE
    headed: bool = False
    listen_seconds: float = 5.0
    settle_ms: int = 1500
    timeout_ms: int = 30000
    batch_size: int = DEFAULT_BATCH
    policy: str = "light"
    no_tournament: bool = False
    no_confirm: bool = False
    reveal: bool = False
    use_cache: bool = True
    cache_path: str = DEFAULT_CACHE_PATH
    json_stdout: bool = False
```

5. **Delete** `parse_args`, `resolve_interactive`, `maybe_act`, `_ask`, `_ask_choice`, and any post-discovery click driven by `--action`.

6. Rename `_main_impl` → `_run_impl(options: FindOptions) -> int` and replace `args.*` with `options.*`. For JSON redirect:

```python
json_out = sys.stdout
if options.json_stdout:
    sys.stdout = sys.stderr
```

Use field `json_stdout` (not `json`, reserved). Never call `maybe_act`. Human print path only prints the result (former `action=print`).

7. Public wrappers:

```python
def run(options: FindOptions) -> int:
    try:
        return _run_impl(options)
    except Exception as exc:
        if options.json_stdout:
            print(
                emit_json_line(
                    build_result(
                        ok=False,
                        url=options.url,
                        final_url=options.url,
                        intent=options.intent,
                        kind=options.kind or "",
                        policy=options.policy,
                        text=str(exc),
                    )
                ),
                file=sys.__stdout__ if False else None,  # see note below
            )
```

Prefer mirroring the existing `main()` try/except in `examples/laya_find.py` (read the current `main` ~lines 1231–1255) and keep the same `_emit_json` / stdout restore behavior — **copy that exact error-handling structure**, only swapping `args` → `options` and `args.json` → `options.json_stdout`.

8. Required validation (url/intent/mode): exit `2` as today.

- [ ] **Step 3: Pass behavior tests**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cli_behavior.py -q
```

Expected: all pass.

- [ ] **Step 4: Commit (optional)**

```powershell
git add src/laya_find/find.py tests/test_cli_behavior.py
git commit -m "refactor: port discovery pipeline to laya_find.find.FindOptions"
```

---

### Task 4: Typer CLI + `__main__`

**Files:**
- Replace: `src/laya_find/cli.py`
- Create: `src/laya_find/__main__.py`
- Create: `tests/test_cli_typer.py`

**Interfaces:**
- Consumes: `FindOptions`, `run` from `laya_find.find`
- Produces: `def main() -> None` (SystemExit with code); Typer `app`

- [ ] **Step 1: Failing CliRunner tests**

`tests/test_cli_typer.py`:

```python
from typer.testing import CliRunner

from laya_find.cli import app


runner = CliRunner()


def test_help_exits_zero():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "url" in result.stdout.lower() or "URL" in result.stdout


def test_missing_required_exits_two():
    result = runner.invoke(app, ["--json"])
    assert result.exit_code == 2
```

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_cli_typer.py -q
```

Expected: FAIL until real Typer app exists (or wrong exit codes).

- [ ] **Step 2: Implement `cli.py`**

```python
from __future__ import annotations

import os
from typing import Optional

import typer

from laya_find.find import DEFAULT_BATCH, DEFAULT_CACHE_PATH, DEFAULT_SERVE, FindOptions, run

app = typer.Typer(
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Encontrar componente/request com Playwright + Laya",
)


@app.callback(invoke_without_command=True)
def find_cmd(
    url: str = typer.Option("", "--url", envvar="LAYA_FIND_URL"),
    intent: str = typer.Option("", "--intent"),
    mode: str = typer.Option("", "--mode", help="dom|network|both"),
    kind: str = typer.Option("", "--kind", help="input|button|link|select|network"),
    serve: str = typer.Option(
        os.environ.get("LAYA_SERVE_URL", DEFAULT_SERVE), "--serve"
    ),
    headed: bool = typer.Option(False, "--headed"),
    listen_seconds: float = typer.Option(5.0, "--listen-seconds"),
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
) -> None:
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
```

Notes for implementer:
- Typer single-command apps often use `@app.command()` on a function named differently, or `typer.Typer` with one command. If `callback(invoke_without_command=True)` fights CliRunner, switch to:

```python
app = typer.Typer(add_completion=False)
@app.command()
def main_cmd(...): ...
def main() -> None:
    app()
```

and point scripts at `main`. Prefer **one** `@app.command()` named so `laya-find --help` shows flags at top level — pattern:

```python
app = typer.Typer(add_completion=False, invoke_without_command=False)

@app.callback()
def _main(...all options...):
    ...
```

If top-level flags are awkward, use the documented Typer pattern for a single-command CLI:

```python
def find(...): ...
app = typer.Typer(add_completion=False)
app.command()(find)  # wrong

# Preferred single-command:
import typer
app = typer.Typer(add_completion=False)

@app.command()
def cli(...):
    ...

def main():
    app()
```

Then users type `laya-find [OPTIONS]` only if using `typer.run(cli)` instead. **Use this pattern (simplest):**

```python
def cli(...options...) -> None:
    ...
    raise typer.Exit(code)

def main() -> None:
    typer.run(cli)
```

And change `pyproject.toml` entry to still `laya_find.cli:main`. For CliRunner tests, export:

```python
app = typer.Typer(add_completion=False)
app.command()(cli)  # if cli is the function — OR build app from typer.main.get_command
```

**Concrete recommended pattern (lock this in):**

```python
app = typer.Typer(add_completion=False, help="...")

@app.callback(invoke_without_command=True)
def _entrypoint(ctx: typer.Context, ...options...):
    if ctx.invoked_subcommand is not None:
        return
    ...
    raise typer.Exit(code)

def main() -> None:
    app()
```

Validate with `laya-find --help` manually in Step 4.

- [ ] **Step 3: `__main__.py`**

```python
from laya_find.cli import main

if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Reinstall + run tests + smoke help**

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest tests\test_cli_typer.py tests\test_cli_behavior.py -q
.\.venv\Scripts\laya-find.exe --help
.\.venv\Scripts\python.exe -m laya_find --help
```

Expected: tests pass; help shows flags; no `--action` / `--interactive`.

- [ ] **Step 5: Commit (optional)**

```powershell
git add src/laya_find/cli.py src/laya_find/__main__.py tests/test_cli_typer.py pyproject.toml
git commit -m "feat: add Typer CLI entry points for laya-find"
```

---

### Task 5: Remove old examples CLI + update demos

**Files:**
- Delete: `examples/laya_find.py`, `examples/laya_find_lib/` (entire dir), `examples/laya_find_heuristic.py`, `examples/__init__.py`
- Modify: `examples/find_demo.ps1`, `examples/hotmart_senha.ps1`
- Modify: `examples/README.md`, `examples/LAYA_FIND.md`

**Interfaces:**
- Consumes: `laya-find` on PATH from venv

- [ ] **Step 1: Update PowerShell demos**

In both `.ps1` files, replace Python script invocation with:

```powershell
$layaFind = Join-Path $PSScriptRoot "..\.venv\Scripts\laya-find.exe"
# fallback:
if (-not (Test-Path $layaFind)) { $layaFind = "laya-find" }

# Keep existing stderr Continue + temp file pattern; call:
$line = & $layaFind --url ... --mode dom --intent ... --json ... 2>$stderrFile
```

Do **not** call `python examples\laya_find.py`.

- [ ] **Step 2: Delete obsolete Python CLI paths**

```powershell
Remove-Item -Recurse -Force C:\laya\examples\laya_find_lib
Remove-Item -Force C:\laya\examples\laya_find.py
Remove-Item -Force C:\laya\examples\laya_find_heuristic.py
Remove-Item -Force C:\laya\examples\__init__.py
```

Keep `fast_triage.py`, `laya_login.py` as experimental demos (update any docstring that points at old find path).

- [ ] **Step 3: Patch examples docs**

`examples/README.md` / `LAYA_FIND.md`: replace all `python examples\laya_find.py` with `laya-find` (or `.\.venv\Scripts\laya-find.exe`). Note `--policy strict` replaces heuristic wrapper. Document cache default `./selector_cache.json`.

- [ ] **Step 4: Full pytest**

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
```

Expected: all green; no imports of `examples.laya_find`.

- [ ] **Step 5: Commit (optional)**

```powershell
git add -A examples tests
git commit -m "chore: remove examples CLI; demos call laya-find"
```

---

### Task 6: Human/agent docs + acceptance

**Files:**
- Modify: `README.md`, `AGENTS.md`, `docs/setup.md`, `docs/architecture.md`, `docs/development.md`, `docs/selectors/cli.md`, `docs/selectors/overview.md`, `docs/README.md` (if links stale)
- Modify: `docs/superpowers/specs/2026-09-26-market-cli-packaging-design.md` status → `implemented` (optional)

- [ ] **Step 1: Update README quickstart**

Replace begin guided block with:

```powershell
cd C:\laya
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
# laya-serve in another terminal (unchanged)
.\.venv\Scripts\laya-find.exe --policy strict --url "https://exemplo.com/" --mode dom --intent "botão de login" --json --settle-ms 3000
```

Update structure tree to `src/laya_find/`.

- [ ] **Step 2: Update AGENTS.md map**

| Área | Onde |
|------|------|
| CLI | `src/laya_find/cli.py` (`laya-find`) |
| Lib | `src/laya_find/` |
| Exemplos | `examples/` (demos only) |

Commands: `laya-find --help`; pytest unchanged.

- [ ] **Step 3: Update docs/setup, architecture, development, selectors/cli**

- setup: `pip install -e ".[dev]"` + playwright install if needed  
- architecture: components point to `src/laya_find`  
- cli.md: Typer flags; no `--action`/`--interactive`; exit codes table from spec  
- development: editable install required before pytest  

- [ ] **Step 4: Acceptance checklist**

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\laya-find.exe --help
.\.venv\Scripts\python.exe -m laya_find --help
.\.venv\Scripts\python.exe -m pytest tests -q
Test-Path C:\laya\examples\laya_find.py   # must be False
Test-Path C:\laya\examples\laya_find_lib  # must be False
```

All criteria from the design spec must hold.

- [ ] **Step 5: Commit (optional)**

```powershell
git add README.md AGENTS.md docs/
git commit -m "docs: document installable laya-find CLI layout"
```

---

## Self-review (plan vs spec)

| Spec requirement | Task |
|------------------|------|
| `src/` + hatchling + `pip install -e .` | 1 |
| Move lib modules | 2 |
| Pipeline + FindOptions; drop action/interactive | 3 |
| Typer + `laya-find` + `python -m` | 4 |
| Remove examples CLI; demos use binary | 5 |
| Docs/AGENTS | 6 |
| Cache cwd default | 3 |
| Exit codes 0/1/2 | 3–4 |
| CliRunner tests | 4 |
| No PyPI / multi-command | — out of scope |

No TBD placeholders left in tasks. Typer single-command pattern has a recommended fallback if `callback` UX fails — implementer must verify `--help` shows options at top level.

# laya-login Implementation Plan

> **For agentic workers:** Execute task-by-task. Spec: [../specs/2026-09-28-laya-login-design.md](../specs/2026-09-28-laya-login-design.md)

**Goal:** `laya-login` wizard: manual headed login → URL/intent → `run_on_page` on same Playwright session; optional `--loop`.

**Architecture:** Extract `run_on_page(page, options)` from `find.py`; `login_flow` + `login_cli`; entry point in `pyproject.toml`.

**Tech Stack:** Typer, Playwright, existing `FindOptions` / `run`.

## Global Constraints

- Same browser session for login + find; no auth.json in MVP
- No auto fill/click credentials
- Preserve `laya-find` public contract
- Exit codes 0/1/2; `--json` stdout contract

---

### Task 1: Extract `run_on_page`

**Files:** Modify `src/laya_find/find.py`; Test: `tests/test_run_on_page.py`

- [ ] Move discovery body into `run_on_page(page, options) -> int` (no launch/close)
- [ ] `_run_impl` launches browser, calls `run_on_page`, closes in `finally`
- [ ] Test: monkeypatch so `run` still works; unit that `run_on_page` is importable and validates missing fields

### Task 2: `login_flow` + `login_cli`

**Files:** Create `login_flow.py`, `login_cli.py`; Modify `pyproject.toml`

- [ ] Wizard: headed → login url → Enter → prompts/flags → `run_on_page` → optional loop
- [ ] Entry `laya-login = laya_find.login_cli:main`

### Task 3: Tests + docs

- [ ] CliRunner `--help`; flow with mocked input/playwright
- [ ] README, AGENTS, cli.md, architecture, examples/README; note on `save_auth.py`

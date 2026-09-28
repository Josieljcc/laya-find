# Design: `laya-login` — login manual + find na mesma sessão

**Data:** 2026-09-28  
**Status:** implemented

## Objetivo

Fluxo interativo esporádico: abrir Chromium headed, usuário faz login manual, depois informar URL + intent e rodar a descoberta **no mesmo browser/contexto Playwright** (cookies/sessão preservados).

**Sucesso:**

```powershell
.\.venv\Scripts\laya-login.exe
# → login URL → Enter após login → URL alvo + intent → JSON/humano do find
.\.venv\Scripts\laya-login.exe --loop
# → repete find na mesma sessão até sair
```

`laya-find` permanece inalterado no contrato público (descoberta sem wizard de login).

## Decisões fechadas

| Tema | Escolha |
|------|---------|
| Sessão | A — um Chromium contínuo (login + find) |
| Exposição | C — binário `laya-login` + lógica no pacote |
| Repetição | C — um find por padrão; `--loop` opcional |
| Integração find | Abordagem 1 — extrair `run_on_page(page, options)` |

## Fora de escopo (MVP)

- Fill/click/submit automático de credenciais
- Persistir `auth.json` / `storage_state` (pode ser follow-up)
- Mudar políticas, torneio ou JSON contract do find
- Substituir o scraper do usuário

## Arquitetura

```
laya-login (login_cli.py)
    → login_flow.run_wizard(...)
         → Playwright headed + page
         → prompt login URL (se preciso) + Enter pós-login
         → prompt / flags: url, intent, mode, …
         → find.run_on_page(page, FindOptions(...))
         → [--loop] até sair
         → fecha browser

laya-find (cli.py)
    → find.run(FindOptions)   # abre browser próprio
         → run_on_page(page, options)
```

| Unidade | Responsabilidade |
|---------|------------------|
| `login_cli.py` | Typer flags, `main()`, entry point |
| `login_flow.py` | Orquestração headed + prompts + loop |
| `find.py` | `run_on_page`; `run` = launch browser + `run_on_page` |
| `cli.py` | Sem mudança de flags públicas |

### Packaging

```toml
[project.scripts]
laya-find = "laya_find.cli:main"
laya-login = "laya_find.login_cli:main"
```

### CLI `laya-login` (flags)

| Flag | Papel |
|------|--------|
| `--login-url` | Página onde o usuário autentica (prompt se vazio) |
| `--url`, `--intent`, `--mode`, `--policy`, … | Mesmas do find quando presentes; senão prompts após login |
| `--json` | Uma linha JSON em stdout (logs stderr) |
| `--loop` | Após um find, pergunta outro URL/intent na mesma sessão |
| `--serve`, `--settle-ms`, `--timeout-ms`, `--batch-size`, `--kind`, cache flags | Repassados ao `FindOptions` |

Prompts usam `input()` no terminal (TTY). Sem TTY e sem flags obrigatórias → exit 2.

### Exit codes

| Code | Quando |
|------|--------|
| 0 | Último find ok |
| 1 | Find falhou (`ok: false`) |
| 2 | Uso/config (URL/intent faltando, serve down, sem TTY) |

Com `--loop`, o exit code reflete o **último** find executado.

## Refactor `find.py`

1. Extrair corpo que hoje assume `page` já navegável para `run_on_page(page, options: FindOptions) -> int`.
2. `run(options)`: `sync_playwright` → browser → new page → `goto` url → `run_on_page` → close (comportamento atual).
3. `login_flow`: após Enter, `page.goto(target_url)` (se diferente) → `run_on_page`.

Não reabrir browser no meio do wizard.

## Testes

- `tests/test_run_on_page.py` (ou estender `test_cli_behavior`): mock page; garante que `run_on_page` é chamado sem launch quando injetado (ou unit do split).
- `tests/test_login_cli.py`: CliRunner `--help` exit 0; missing required sem TTY → exit 2 (se aplicável).
- `tests/test_login_flow.py`: monkeypatch `input` + mock playwright — verifica ordem: login url → wait → find prompts (sem browser real se possível).
- Suite existente de find continua verde.

## Docs

Atualizar: `README.md`, `AGENTS.md`, `docs/selectors/cli.md`, `docs/architecture.md`, `examples/README.md`.  
`examples/save_auth.py`: nota apontando para `laya-login` como fluxo preferido para “login + find”.

## Critérios de aceite

1. `pip install -e ".[dev]"` expõe `laya-login` e `laya-find`.
2. `laya-login --help` funciona.
3. Fluxo manual headed: login → Enter → URL + intent → seletor (página autenticada).
4. Sem `--loop`: um find e fecha.
5. Com `--loop`: segundo intent na mesma sessão sem novo login.
6. `pytest tests -q` verde.
7. `laya-find` contrato e flags públicos preservados.

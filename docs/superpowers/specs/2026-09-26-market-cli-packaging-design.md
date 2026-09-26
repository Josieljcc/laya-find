# Design: CLI instalável no padrão Python open source

**Data:** 2026-09-26  
**Status:** implemented
**Escopo:** packaging local + Typer + layout `src/` — **não** inclui publicar no PyPI

## Objetivo

Transformar o descobridor atual (`examples/laya_find.py` + `examples/laya_find_lib/`) numa CLI instalável no padrão PyPA, alinhada a projetos open source Python, sem mudar o comportamento de descoberta (Playwright → política → torneio Laya → JSON).

**Sucesso:**

```powershell
pip install -e ".[dev]"
laya-find --url "https://exemplo.com/" --mode dom --intent "botão de login" --json
# ou: python -m laya_find ...
```

Stdout = uma linha JSON; logs em stderr. Testes passam importando `laya_find`.

## Decisões fechadas

| Tema | Escolha |
|------|---------|
| Meta | A — instalável local (`pip install -e .`), não PyPI ainda |
| Framework CLI | B — Typer |
| Superfície | A — um comando `laya-find` (sem subcomandos) |
| `examples/` | B — remover CLI de `examples/`; só demos que invocam `laya-find` |
| Layout | Abordagem 1 — `src/laya_find/` |

## Arquitetura alvo

```
C:\laya\
  pyproject.toml
  README.md
  AGENTS.md
  src/
    laya_find/
      __init__.py          # __version__
      __main__.py          # python -m laya_find → cli.app()
      cli.py               # Typer app + flags
      find.py              # orquestração (lógica hoje em laya_find.py)
      selectors.py
      policy.py
      normalize.py
      decide.py
      cache.py
      contract.py
  examples/                # demos apenas (.ps1, docs cookbook)
  tests/
  docs/
```

### Responsabilidades

| Unidade | Faz | Não faz |
|---------|-----|---------|
| `cli.py` | Parse Typer, exit codes, wiring stderr/stdout | Coleta DOM / Laya |
| `find.py` | Pipeline de descoberta (browser, torneio, cache) | Argument parsing |
| módulos lib | Seletores, policy, contract, etc. | I/O de CLI |
| `examples/*.ps1` | Cookbook / demos | Lógica de produto |

### Packaging (`pyproject.toml`)

- Build backend: **hatchling** (padrão comum e simples com `src/`).
- `[project]`: `name = "laya-find"`, `version` alinhada a `__version__`, `requires-python = ">=3.10"`.
- Dependencies: `laya[serve]`, `playwright`, `typer`.
- Optional `[project.optional-dependencies] dev`: `pytest`, `ruff` (opcional).
- Entry point: `[project.scripts] laya-find = "laya_find.cli:main"` onde `cli.py` define `app = typer.Typer(...)` e `def main() -> None: app()`. `__main__.py` chama `main()`.
- Cache default: path estável sob cwd do usuário ou `Path.home()` / env — **decisão:** default `./selector_cache.json` no cwd (comportamento previsível para scrapers); scripts de exemplo podem passar `--cache-path`. O arquivo antigo em `examples/selector_cache.json` deixa de ser o default; `.gitignore` cobre `selector_cache.json` na raiz e em `examples/`.

### Typer / contrato CLI

Flags preservadas (mesmos nomes e defaults atuais, salvo remoções abaixo):

- `--url`, `--intent`, `--mode`, `--kind`, `--serve`, `--headed`
- `--listen-seconds`, `--settle-ms`, `--timeout-ms`, `--batch-size`
- `--policy {none,light,strict}`, `--no-tournament`, `--no-confirm`, `--reveal`
- `--use-cache` / `--no-cache`, `--cache-path`, `--json`

**Removidos da CLI pública:**

- `--action click|ask|print` — descoberta sempre “print” (stdout humano ou JSON); ações ficam no scraper.
- `--interactive` — fora do contrato de discoverability.

**Exit codes:**

| Code | Quando |
|------|--------|
| 0 | Descoberta ok (`ok: true` no JSON, ou print humano bem-sucedido) |
| 1 | Descoberta falhou (`ok: false`) ou nenhum candidato |
| 2 | Erro de uso/config (serve inacessível, URL/intent faltando, etc.) |

**`--json`:** Typer/Rich não escrevem logs no stdout; helpers de log vão para stderr.

### Migração de `examples/`

- Apagar: `examples/laya_find.py`, `examples/laya_find_lib/`, `examples/laya_find_heuristic.py`, `examples/__init__.py` (se só existia para imports).
- Manter/ajustar: `find_demo.ps1`, `hotmart_senha.ps1`, `LAYA_FIND.md`, `README.md`, demos experimentais (`fast_triage.py`, `laya_login.py`) que **não** são a CLI find — podem continuar como scripts soltos ou `python examples/...` sem serem o produto.
- Scripts `.ps1` chamam `laya-find` (PATH do venv) com o mesmo tratamento de stderr já introduzido.

### Testes

- Remover dependência de `pythonpath = .` para achar `examples.*`.
- Imports: `from laya_find.selectors import ...` etc.
- Novo: `tests/test_cli_typer.py` com `CliRunner` — `--help` exit 0; invocação mínima com browser mockado ou flag que falha cedo com exit 2 (serve down) sem Chromium.
- Suite unitária existente continua cobrindo lib.

### Docs a atualizar

`README.md`, `AGENTS.md`, `docs/setup.md`, `docs/architecture.md`, `docs/development.md`, `docs/selectors/cli.md`, `docs/selectors/overview.md`, `examples/LAYA_FIND.md`, `examples/README.md`.

### Fora de escopo

- Publicar PyPI, trocar de nome no índice, LICENSE formal, CI de release.
- Multi-comando (`laya find`, `cache clear`).
- Mudança de políticas, torneio, JSON contract fields (exceto remoção de flags legadas na CLI).
- Implementar fill/click/login no find.

### `.gitignore`

Acrescentar: `dist/`, `build/`, `*.egg-info/`, `src/*.egg-info/`, `selector_cache.json` (raiz).

## Riscos e mitigação

| Risco | Mitigação |
|-------|-----------|
| Typer muda help/UX vs argparse | Mapear flags 1:1; testes de `--help` e smoke JSON |
| Scripts externos ainda apontam para `examples/laya_find.py` | Docs + AGENTS; sem shim (decisão B) |
| Cache path muda de `examples/` | Documentar; `--cache-path`; gitignore |
| `laya_find.py` monolítico (~48KB) | Extrair parsing para `cli.py`, pipeline para `find.py` sem big-bang de lógica |

## Critérios de aceite

1. `pip install -e ".[dev]"` no venv funciona.
2. `laya-find --help` e `python -m laya_find --help` funcionam.
3. `pytest tests -q` verde.
4. Nenhum `examples/laya_find.py` / `laya_find_lib` no tree.
5. Docs e `.ps1` usam `laya-find`.
6. Contrato JSON e políticas inalterados no comportamento.

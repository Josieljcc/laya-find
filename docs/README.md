# Documentação

Mapa para humanos e agentes. Prefira este índice a vasculhar o repo à cegas.

## Entrada

| Audiência | Documento |
|-----------|-----------|
| Visão geral | [../README.md](../README.md) |
| Agentes (regras + links) | [../AGENTS.md](../AGENTS.md) |

## Guias

| Doc | Conteúdo |
|-----|----------|
| [setup.md](setup.md) | venv, install editável, Playwright, `laya-serve` |
| [architecture.md](architecture.md) | fluxo `laya-find` / `laya-login` → Laya → JSON; módulos em `src/laya_find/` |
| [development.md](development.md) | testes, layout, como contribuir |
| [selectors/overview.md](selectors/overview.md) | papel do find vs scraper; kinds |
| [selectors/cli.md](selectors/cli.md) | flags `laya-find` + `laya-login`; `clickable` / `image` |
| [selectors/json-contract.md](selectors/json-contract.md) | schema `--json` |
| [selectors/policies.md](selectors/policies.md) | `none` / `light` / `strict` |
| [selectors/cache.md](selectors/cache.md) | cache de seletores |

## Cookbooks / exemplos

| Doc | Conteúdo |
|-----|----------|
| [../examples/README.md](../examples/README.md) | Índice dos scripts de exemplo |
| [../examples/LAYA_FIND.md](../examples/LAYA_FIND.md) | PowerShell + scraper consomem `--json` |
| [../examples/find_demo.ps1](../examples/find_demo.ps1) | Demo find genérico (JSON) |
| [../examples/hotmart_senha.ps1](../examples/hotmart_senha.ps1) | Demo find senha Hotmart (`--reveal`) |
| [../examples/save_auth.py](../examples/save_auth.py) | Demo: login manual → `auth.json` (preferir `laya-login` para find) |
| [../examples/fast_triage.py](../examples/fast_triage.py) | Demo triage via `laya-serve` (sem Playwright) |
| [../examples/laya_login.py](../examples/laya_login.py) | Demo login fill+click (experimental) |

## Planos / histórico

| Doc | Conteúdo |
|-----|----------|
| [superpowers/specs/2026-09-28-laya-login-design.md](superpowers/specs/2026-09-28-laya-login-design.md) | design `laya-login` |
| [superpowers/plans/2026-09-28-laya-login.md](superpowers/plans/2026-09-28-laya-login.md) | plano `laya-login` |
| [superpowers/plans/2026-09-26-laya-selector-discoverability.md](superpowers/plans/2026-09-26-laya-selector-discoverability.md) | plano de encontrabilidade |
| [superpowers/plans/2026-09-26-market-cli-packaging.md](superpowers/plans/2026-09-26-market-cli-packaging.md) | packaging CLI (`src/`) |

## Upstream

- Laya: https://github.com/NandhaKishorM/laya  
- Docs Laya: https://nandhakishorm.github.io/laya/

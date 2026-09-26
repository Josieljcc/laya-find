# Laya Find Workspace

Workspace local em torno do [Laya](https://github.com/NandhaKishorM/laya): motor de decisões tipadas (choice / score / noul) + ferramentas para **descobrir seletores DOM estáveis** e alimentar um scraper externo.

## O que este repo faz

| Peça | Função |
|------|--------|
| **`laya-serve`** | HTTP API de inferência (`/v1/systemone`, `/health`) |
| **`laya_find`** | Dado URL + intent → JSON com `selector` estável (não executa o scrape) |
| **Seu scraper** | Usa o seletor devolvido (Playwright, Selenium, etc.) |

**Fora de escopo do find:** fill, click de submit, login E2E. Isso fica no seu scraper.

## Início rápido

```powershell
cd C:\laya

# 1) Ambiente (já criado: .venv com laya + playwright)
# Se precisar recriar: py -3.12 -m venv .venv
# .\.venv\Scripts\python.exe -m pip install "laya[serve]" playwright pytest
# .\.venv\Scripts\python.exe -m playwright install chromium

# 2) Servidor Laya (outro terminal)
$env:LAYA_HOST='127.0.0.1'; $env:LAYA_PORT='8000'
$env:LAYA_PRELOAD='1'; $env:LAYA_MODELS='multilingual'; $env:LAYA_DEVICE='cpu'
.\.venv\Scripts\laya-serve.exe

# 3) Descobrir seletor
$env:PYTHONIOENCODING='utf-8'
.\.venv\Scripts\python.exe examples\laya_find.py `
  --policy strict `
  --url "https://exemplo.com/" `
  --mode dom `
  --intent "botão de login" `
  --json `
  --settle-ms 3000
```

Stdout = uma linha JSON. Logs = stderr. Detalhes: [docs/selectors/json-contract.md](docs/selectors/json-contract.md).

## Documentação

| Para | Comece em |
|------|-----------|
| Humanos (visão geral) | Este README |
| Agentes de código | [AGENTS.md](AGENTS.md) |
| Índice de docs | [docs/README.md](docs/README.md) |
| Setup / ambiente | [docs/setup.md](docs/setup.md) |
| Arquitetura | [docs/architecture.md](docs/architecture.md) |
| Integração scraper | [examples/LAYA_FIND.md](examples/LAYA_FIND.md) |
| Desenvolvimento / testes | [docs/development.md](docs/development.md) |

## Estrutura

```
examples/
  README.md                 # índice dos exemplos
  laya_find.py              # CLI principal
  laya_find_heuristic.py    # wrapper → --policy strict
  laya_find_lib/            # selectors, policy, cache, contract, …
  LAYA_FIND.md              # cookbook scraper ↔ find
  find_demo.ps1 / hotmart_senha.ps1
  fast_triage.py / laya_login.py   # demos Laya (login = experimental)
docs/
  …                         # guias humanos + agentes
tests/                      # pytest
```

Índice dos exemplos: [examples/README.md](examples/README.md).
## Requisitos

- Python 3.10+ (recomendado 3.12)
- `laya[serve]`, Playwright Chromium
- Acesso Hugging Face na 1ª carga de checkpoint (cache local depois)

Upstream Laya: https://github.com/NandhaKishorM/laya · Docs: https://nandhakishorm.github.io/laya/

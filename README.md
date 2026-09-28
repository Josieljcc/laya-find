# Laya Find Workspace

Workspace local em torno do [Laya](https://github.com/NandhaKishorM/laya): motor de decisões tipadas (choice / score / noul) + ferramentas para **descobrir seletores DOM estáveis** e alimentar um scraper externo.

## O que este repo faz

| Peça | Função |
|------|--------|
| **`laya-serve`** | HTTP API de inferência (`/v1/systemone`, `/health`) |
| **`laya-find`** | Dado URL + intent → JSON com `selector` estável (não executa o scrape) |
| **`laya-login`** | Login **manual** headed, depois find na **mesma** sessão Playwright |
| **Seu scraper** | Usa o seletor devolvido (Playwright, Selenium, etc.) |

**Fora de escopo do find:** fill/click/submit automático. `laya-login` só espera o login humano (Enter).

## Início rápido

Setup completo (Linux / macOS / Windows): [docs/setup.md](docs/setup.md).

Com o venv ativo (`source .venv/bin/activate` ou `.\.venv\Scripts\Activate.ps1`):

```bash
python -m pip install -e ".[dev]"
python -m playwright install chromium

# 2) Servidor Laya (outro terminal; export LAYA_* no bash ou $env: no PowerShell)
export LAYA_HOST=127.0.0.1 LAYA_PORT=8000 LAYA_PRELOAD=1
export LAYA_MODELS=multilingual LAYA_DEVICE=cpu
laya-serve

# 3) Descobrir seletor
laya-find --policy strict --url "https://exemplo.com/" --mode dom \
  --intent "botão de login" --json --settle-ms 3000

# 3b) Página atrás de login (manual na janela + find na mesma sessão)
laya-login --login-url "https://exemplo.com/login"
# opcional: --url / --intent / --json / --loop
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
src/laya_find/
  cli.py                    # Typer / entry point laya-find
  login_cli.py / login_flow.py  # laya-login (login manual + find)
  find.py                   # run / run_on_page (Playwright → Laya → JSON)
  selectors.py, policy.py   # lógica testável
  cache.py, contract.py, …
examples/
  README.md                 # índice dos exemplos
  LAYA_FIND.md              # cookbook scraper ↔ find
  find_demo.ps1 / hotmart_senha.ps1 / save_auth.py
  fast_triage.py / laya_login.py   # demos apenas
docs/
  …                         # guias humanos + agentes
tests/                      # pytest
```

Kinds DOM: `input` | `button` | `link` | `select` | `clickable` | `image` (+ `network`). Ver [docs/selectors/cli.md](docs/selectors/cli.md).

Índice dos exemplos: [examples/README.md](examples/README.md).
## Requisitos

- Python 3.10+ (recomendado 3.12)
- `laya[serve]`, Playwright Chromium
- Acesso Hugging Face na 1ª carga de checkpoint (cache local depois)

Upstream Laya: https://github.com/NandhaKishorM/laya · Docs: https://nandhakishorm.github.io/laya/

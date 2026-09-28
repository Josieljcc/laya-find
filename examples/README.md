# Exemplos

Índice dos scripts em `examples/`. Documentação completa: [../docs/README.md](../docs/README.md) · [../AGENTS.md](../AGENTS.md).

| Script | Status | O que faz |
|--------|--------|-----------|
| [`LAYA_FIND.md`](LAYA_FIND.md) | Atual | Cookbook scraper ↔ `laya-find --json` (bash + PowerShell) |
| [`hotmart_senha.ps1`](hotmart_senha.ps1) | Atual | Demo find: senha na Hotmart (`--reveal`) — Windows |
| [`find_demo.ps1`](find_demo.ps1) | Atual | Demo find genérico + JSON — Windows |
| [`save_auth.py`](save_auth.py) | Atual | Login manual → `auth.json` (para find autenticado prefira `laya-login`) |
| [`fast_triage.py`](fast_triage.py) | Atual | Demo Laya serve (triage, sem Playwright) |
| [`laya_login.py`](laya_login.py) | Experimental | Login fill+click; para seletores prefira `laya-find` / `laya-login` |

CLIs do pacote (`pip install -e .` — ver [../docs/setup.md](../docs/setup.md)):

- **`laya-find`** — descoberta de seletores  
- **`laya-login`** — login manual headed + find na mesma sessão  

Política agressiva: `--policy strict`. Kinds extras: `--kind clickable`, `--kind image` — ver [../docs/selectors/cli.md](../docs/selectors/cli.md).

## Pré-requisito comum

`laya-serve` em `http://127.0.0.1:8000` — ver [../docs/setup.md](../docs/setup.md).

```bash
cd /caminho/para/laya-find
# Linux/macOS:
source .venv/bin/activate
# Windows PowerShell: .\.venv\Scripts\Activate.ps1
```

## Comandos rápidos

Com o venv ativo (qualquer OS):

```bash
# Find (scraper) — cache padrão ./selector_cache.json no cwd
laya-find --policy strict --url "URL" --mode dom --intent "..." --json --settle-ms 3000

# Página atrás de login (manual) + find
laya-login --login-url "https://site/login"

# Collapse / div clicável
laya-find --url "URL" --mode dom --intent "cabeçalho collapse" --kind clickable --json

# Imagens
laya-find --url "URL" --mode dom --intent "imagem do módulo" --kind image --json

# Triage HTTP
python examples/fast_triage.py
```

Demos PowerShell (Windows): `./examples/hotmart_senha.ps1`, `./examples/find_demo.ps1`.

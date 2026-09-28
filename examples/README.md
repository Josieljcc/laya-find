# Exemplos

Índice dos scripts em `examples/`. Documentação completa: [../docs/README.md](../docs/README.md) · [../AGENTS.md](../AGENTS.md).

| Script | Status | O que faz |
|--------|--------|-----------|
| [`LAYA_FIND.md`](LAYA_FIND.md) | Atual | Cookbook scraper ↔ `laya-find --json` |
| [`hotmart_senha.ps1`](hotmart_senha.ps1) | Atual | Demo find: senha na Hotmart (`--reveal`) |
| [`find_demo.ps1`](find_demo.ps1) | Atual | Demo find genérico + JSON |
| [`save_auth.py`](save_auth.py) | Atual | Login manual → `auth.json` (para find autenticado prefira `laya-login`) |
| [`fast_triage.py`](fast_triage.py) | Atual | Demo Laya serve (triage, sem Playwright) |
| [`laya_login.py`](laya_login.py) | Experimental | Login fill+click; para seletores prefira `laya-find` / `laya-login` |

CLIs do pacote (`pip install -e .`):

- **`laya-find`** — descoberta de seletores  
- **`laya-login`** — login manual headed + find na mesma sessão  

Política agressiva: `--policy strict`. Kinds extras: `--kind clickable`, `--kind image` — ver [../docs/selectors/cli.md](../docs/selectors/cli.md).

## Pré-requisito comum

`laya-serve` em `http://127.0.0.1:8000` — ver [../docs/setup.md](../docs/setup.md).

```powershell
cd C:\laya
$env:PYTHONIOENCODING='utf-8'
```

## Comandos rápidos

```powershell
# Find (scraper) — cache padrão ./selector_cache.json no cwd
.\.venv\Scripts\laya-find.exe --policy strict --url "URL" --mode dom --intent "..." --json --settle-ms 3000

# Página atrás de login (manual) + find
.\.venv\Scripts\laya-login.exe --login-url "https://site/login"

# Collapse / div clicável
.\.venv\Scripts\laya-find.exe --url "URL" --mode dom --intent "cabeçalho collapse" --kind clickable --json

# Imagens
.\.venv\Scripts\laya-find.exe --url "URL" --mode dom --intent "imagem do módulo" --kind image --json

# Hotmart senha
.\examples\hotmart_senha.ps1

# Triage HTTP
.\.venv\Scripts\python.exe examples\fast_triage.py
```

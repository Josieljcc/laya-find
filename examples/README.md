# Exemplos

Índice dos scripts em `examples/`. Documentação completa: [../docs/README.md](../docs/README.md) · [../AGENTS.md](../AGENTS.md).

| Script | Status | O que faz |
|--------|--------|-----------|
| [`LAYA_FIND.md`](LAYA_FIND.md) | Atual | Cookbook scraper ↔ `laya-find --json` |
| [`hotmart_senha.ps1`](hotmart_senha.ps1) | Atual | Demo find: senha na Hotmart (`--reveal`) |
| [`find_demo.ps1`](find_demo.ps1) | Atual | Demo find genérico + JSON |
| [`fast_triage.py`](fast_triage.py) | Atual | Demo Laya serve (triage, sem Playwright) |
| [`laya_login.py`](laya_login.py) | Experimental | Login fill+click; para seletores prefira `laya-find` |

A CLI de descoberta é **`laya-find`** (pacote `laya_find` em `src/`). Instale o projeto no venv (`pip install -e .`) e use `.\.venv\Scripts\laya-find.exe` ou `python -m laya_find`. Política agressiva: `--policy strict` (substitui o antigo wrapper heurístico).

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

# Hotmart senha
.\examples\hotmart_senha.ps1

# Triage HTTP
.\.venv\Scripts\python.exe examples\fast_triage.py
```

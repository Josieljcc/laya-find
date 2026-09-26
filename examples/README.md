# Exemplos

Índice dos scripts em `examples/`. Documentação completa: [../docs/README.md](../docs/README.md) · [../AGENTS.md](../AGENTS.md).

| Script | Status | O que faz |
|--------|--------|-----------|
| [`laya_find.py`](laya_find.py) | **Atual** | CLI de descoberta de seletores (use esta) |
| [`laya_find_heuristic.py`](laya_find_heuristic.py) | Wrapper | Equivale a `laya_find.py --policy strict` |
| [`LAYA_FIND.md`](LAYA_FIND.md) | Atual | Cookbook scraper ↔ `--json` |
| [`hotmart_senha.ps1`](hotmart_senha.ps1) | Atual | Demo find: senha na Hotmart (`--reveal`) |
| [`find_demo.ps1`](find_demo.ps1) | Atual | Demo find genérico + JSON |
| [`fast_triage.py`](fast_triage.py) | Atual | Demo Laya serve (triage, sem Playwright) |
| [`laya_login.py`](laya_login.py) | Experimental | Login fill+click; para seletores prefira `laya_find` |

## Pré-requisito comum

`laya-serve` em `http://127.0.0.1:8000` — ver [../docs/setup.md](../docs/setup.md).

```powershell
cd C:\laya
$env:PYTHONIOENCODING='utf-8'
```

## Comandos rápidos

```powershell
# Find (scraper)
.\.venv\Scripts\python.exe examples\laya_find.py --policy strict --url "URL" --mode dom --intent "..." --json --settle-ms 3000

# Hotmart senha
.\examples\hotmart_senha.ps1

# Triage HTTP
.\.venv\Scripts\python.exe examples\fast_triage.py
```

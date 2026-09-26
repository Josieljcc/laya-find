# CLI — `laya_find`

```powershell
.\.venv\Scripts\python.exe examples\laya_find.py --help
```

Wrapper legado: `examples\laya_find_heuristic.py` ≡ `--policy strict`.

## Flags principais

| Flag | Default | Descrição |
|------|---------|-----------|
| `--url` | (obrigatório sem interativo) | Página |
| `--intent` | (obrigatório) | O que procurar |
| `--mode` | (obrigatório) | `dom` \| `network` \| `both` |
| `--policy` | `light` | `none` \| `light` \| `strict` — [policies.md](policies.md) |
| `--kind` | (auto) | Força `input`/`button`/`link`/`select`/`network` |
| `--json` | off | Uma linha JSON em stdout; logs em stderr; força `--action print` |
| `--action` | `ask` | `print` (scraper) \| `click`/`ask` (legado) |
| `--settle-ms` | `1500` | Espera pós-load |
| `--batch-size` | `10` | Tamanho do lote no torneio Laya |
| `--serve` | `http://127.0.0.1:8000` | Base do `laya-serve` |
| `--headed` | off | Browser visível |
| `--reveal` | off | Opt-in: tenta clicar Entrar/Login para revelar campos |
| `--no-confirm` | off | Pula noul final |
| `--no-tournament` | off | Uma choice limitada ao batch |
| `--use-cache` / `--no-cache` | cache on | [cache.md](cache.md) |
| `--cache-path` | `examples/selector_cache.json` | Arquivo de cache |
| `--listen-seconds` | `5` | Duração da escuta network |
| `--interactive` | off | Força prompts |

## Exemplos

**Scraper (recomendado):**

```powershell
.\.venv\Scripts\python.exe examples\laya_find.py `
  --policy strict --url "https://site/" --mode dom `
  --intent "campo de email" --json --settle-ms 3000
```

**Humano / debug:**

```powershell
.\.venv\Scripts\python.exe examples\laya_find.py `
  --policy light --url "https://site/" --mode dom `
  --intent "botão de login" --action print --headed --settle-ms 3000
```

## Interativo

Sem `--url`/`--intent`/`--mode` (e sem `--json`), a CLI pergunta. Com `--json`, flags incompletas → JSON `ok:false` e exit 2 (sem prompt).

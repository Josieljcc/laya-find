# CLI — `laya-find`

```powershell
.\.venv\Scripts\laya-find.exe --help
# equivalente:
.\.venv\Scripts\python.exe -m laya_find --help
```

A CLI usa Typer, possui um único comando e é instalada pelo projeto. Execute `pip install -e ".[dev]"` antes do primeiro uso.

## Flags principais

| Flag | Default | Descrição |
|------|---------|-----------|
| `--url` | (obrigatório) | Página; também aceita `LAYA_FIND_URL` |
| `--intent` | (obrigatório) | O que procurar |
| `--mode` | (obrigatório) | `dom` \| `network` \| `both` |
| `--policy` | `light` | `none` \| `light` \| `strict` — [policies.md](policies.md) |
| `--kind` | (auto) | Força `input`/`button`/`link`/`select`/`network` |
| `--json` | off | Uma linha JSON em stdout; logs em stderr |
| `--settle-ms` | `1500` | Espera pós-load |
| `--timeout-ms` | `30000` | Timeout Playwright |
| `--batch-size` | `10` | Tamanho do lote no torneio Laya |
| `--serve` | `http://127.0.0.1:8000` | Base do `laya-serve` |
| `--headed` | off | Browser visível |
| `--reveal` | off | Opt-in: tenta clicar Entrar/Login para revelar campos |
| `--no-confirm` | off | Pula noul final |
| `--no-tournament` | off | Uma choice limitada ao batch |
| `--use-cache` / `--no-cache` | cache on | [cache.md](cache.md) |
| `--cache-path` | `selector_cache.json` | Arquivo de cache relativo ao cwd |
| `--listen-seconds` | `5` | Duração da escuta network |

`--action` e `--interactive` foram removidos. A descoberta sempre imprime o resultado; fill, click e submit pertencem ao scraper externo. A CLI não solicita valores interativamente: `--url`, `--intent` e `--mode` ausentes são erro de uso.

## Códigos de saída

| Código | Quando |
|--------|--------|
| `0` | Descoberta concluída (`ok:true` em JSON) |
| `1` | Descoberta falhou (`ok:false`), inclusive nenhum candidato |
| `2` | Erro de uso/configuração, como argumentos obrigatórios ausentes/inválidos ou `laya-serve` inacessível |

## Exemplos

**Scraper (recomendado):**

```powershell
.\.venv\Scripts\laya-find.exe `
  --policy strict --url "https://site/" --mode dom `
  --intent "campo de email" --json --settle-ms 3000
```

**Humano / debug:**

```powershell
.\.venv\Scripts\laya-find.exe `
  --policy light --url "https://site/" --mode dom `
  --intent "botão de login" --headed --settle-ms 3000
```

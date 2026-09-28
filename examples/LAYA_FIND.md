# Integração: `laya_find` → seu scraper

Guia prático (cookbook). Visão geral do repo: [../README.md](../README.md) · Agentes: [../AGENTS.md](../AGENTS.md) · Índice: [../docs/README.md](../docs/README.md).

Docs específicos:

- Overview: [../docs/selectors/overview.md](../docs/selectors/overview.md)
- CLI: [../docs/selectors/cli.md](../docs/selectors/cli.md)
- JSON: [../docs/selectors/json-contract.md](../docs/selectors/json-contract.md)
- Políticas: [../docs/selectors/policies.md](../docs/selectors/policies.md)
- Cache: [../docs/selectors/cache.md](../docs/selectors/cache.md)
- Setup: [../docs/setup.md](../docs/setup.md)

---

Guia para usar o descobridor de seletores sem acoplar login, fill ou submit ao find.

## Papel do `laya_find`

`laya_find` faz **somente encontrabilidade**: dado uma URL, um modo (`dom` / `network` / `both`) e um intent em linguagem natural, devolve o melhor candidato (principalmente `selector`, mais `href`, `text`, scores).

Seu scraper (Playwright, Selenium, HTTP, etc.) **continua responsável** por navegar, preencher campos, clicar e persistir dados. A descoberta não clica por padrão. `--reveal` é um opt-in que tenta clicar em um controle Entrar/Login para revelar campos ocultos.

Use `--json` no contrato suportado (uma linha JSON em stdout).

Pré-requisito: `laya-serve` em `http://127.0.0.1:8000` (ou `LAYA_SERVE_URL`). Setup: [../docs/setup.md](../docs/setup.md).

## Bash / zsh consumindo `--json` (Linux / macOS)

Logs humanos vão para **stderr**; **stdout** é uma única linha JSON.

```bash
cd /caminho/para/laya-find
source .venv/bin/activate

line=$(laya-find \
  --url "https://exemplo.com/login" \
  --mode dom \
  --intent "campo de senha" \
  --policy light \
  --json \
  --settle-ms 3000 \
  2>/tmp/laya-find.err)

cat /tmp/laya-find.err >&2   # opcional: ver logs
echo "$line" | python -c 'import json,sys; r=json.load(sys.stdin); print(r.get("selector"), r.get("ok"))'
```

Campos úteis do contrato: `selector`, `selector_ok`, `matches`, `href`, `text`, `confidence`, `confirm_noul`, `policy`, `cached`, `final_url`.

## PowerShell consumindo `--json` (Windows)

Logs humanos vão para **stderr**; **stdout** é uma única linha JSON (ideal para `ConvertFrom-Json`).

> **PowerShell:** com `$ErrorActionPreference = 'Stop'`, texto em stderr do CLI vira `NativeCommandError`. Nos scripts `*.ps1` do repo isso já é tratado (`Continue` só na chamada). Em one-liners manuais, use `$ErrorActionPreference = 'Continue'` em volta do `& laya-find ...` ou redirecione `2>logs.txt`.

```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\..   # ou o path do clone
$env:PYTHONIOENCODING = "utf-8"
.\.venv\Scripts\Activate.ps1
$layaFind = "laya-find"

# Descobrir seletor (não clica)
$stderrFile = [System.IO.Path]::GetTempFileName()
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $line = & $layaFind `
      --url "https://exemplo.com/login" `
      --mode dom `
      --intent "campo de senha" `
      --policy light `
      --json `
      --settle-ms 3000 `
      2>$stderrFile
} finally {
    $ErrorActionPreference = $prevEap
}
Get-Content $stderrFile -ErrorAction SilentlyContinue
Remove-Item $stderrFile -Force -ErrorAction SilentlyContinue

$result = $line | ConvertFrom-Json
```

Ou use o script pronto: [`find_demo.ps1`](find_demo.ps1) / [`hotmart_senha.ps1`](hotmart_senha.ps1).

```powershell
# Alternativa curta se preferir one-liner sem Stop na chamada nativa:
# ver find_demo.ps1
```

Campos úteis do contrato: `selector`, `selector_ok`, `matches`, `href`, `text`, `confidence`, `confirm_noul`, `policy`, `cached`, `final_url`.

## Política: `--policy none` vs `light` vs `strict`

| Política | O que faz | Quando usar |
|----------|-----------|-------------|
| **`light`** (padrão) | Dedupe + ranking suave por tokens do intent (CTAs prováveis sobem, nada é descartado cedo) | Maioria dos sites; intent genérico (“botão entrar”, “link cadastro”) |
| **`strict`** | Dedupe + **filtro agressivo** (senha → só `type=password`, email → campos email, login vs cadastro) + ranking | Páginas barulhentas (muitos links/CTAs); intents claros (“campo senha”, “email login”, “cadastrar agora”) |
| **`none`** | Só dedupe; torneio Laya em lotes embaralhados **sem** ranking heurístico | Quando `light`/`strict` empurram o candidato errado para o topo, ou você quer decisão quase puramente Laya |

Troque de política antes de aumentar `--batch-size` ou desligar confirmação.

## Cache de seletores

| Item | Detalhe |
|------|---------|
| **Arquivo padrão** | `./selector_cache.json` no diretório de trabalho (cwd) |
| **Chave** | `host[:port]::intent normalizado` — mesmo host compartilha CTAs entre URLs |
| **Gravação** | Só seletores DOM verificados, estáveis (não voláteis), com `--use-cache` (padrão) |
| **Hit** | Revalida o seletor na página; se falhar, a entrada é removida automaticamente |

**Invalidar / forçar redescoberta**

- Uma execução: `--no-cache` (ignora leitura e **não grava**).
- Só esta combinação site+intent: apague a chave correspondente em `selector_cache.json`, ou delete o arquivo inteiro.
- Outro caminho: `--cache-path /caminho/outro_cache.json` (Windows: `C:\caminho\outro_cache.json`).

Na 2ª visita bem-sucedida, espere `"cached": true` no JSON e tempo bem menor que a 1ª run.

## Limitações conhecidas

1. **Lotes grandes** — O torneio Laya processa candidatos em lotes (padrão `--batch-size 10`). Com dezenas/centenas de candidatos DOM, latência sobe e a escolha pode degradar; reduza ruído com `--policy strict` ou coleta mais focada (`--kind`).
2. **noul otimista** — A confirmação final (`confirm_noul`) pode marcar “atende o intent” com confiança alta em CTAs parecidos (ex.: Ajuda vs Cadastrar). Trate `confirm_noul < 0.5` como sinal de revisão manual; use `--no-confirm` só se você aceitar o risco.
3. **`none` pode errar** — Sem ranking, o torneio depende mais do acaso de embaralhamento e do tamanho do pool; útil para depuração, não como padrão em produção.
4. **Cache por host** — Intent igual em páginas diferentes do mesmo site pode reutilizar seletor inadequado; invalide o cache após redesign.
5. **Fora de escopo do find** — Cadeias fill/click/submit automáticas não fazem parte do `laya-find`. Para página autenticada: use **`laya-login`** (login manual + find na mesma sessão) — ver [docs/selectors/cli.md](../docs/selectors/cli.md).

## Referências

- Índice exemplos: [README.md](README.md)
- CLI: `laya-find --help` / `laya-login --help` · [docs/selectors/cli.md](../docs/selectors/cli.md)
- Demos: [find_demo.ps1](find_demo.ps1), [hotmart_senha.ps1](hotmart_senha.ps1), [save_auth.py](save_auth.py)
- Plano: [docs/superpowers/plans/2026-09-26-laya-selector-discoverability.md](../docs/superpowers/plans/2026-09-26-laya-selector-discoverability.md)
- Upstream Laya: https://github.com/NandhaKishorM/laya

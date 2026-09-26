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

Use `--action print` ou `--json` no contrato suportado. `--action click` e `--action ask` são opções legadas, fora do contrato de scraper, e podem clicar após a descoberta.

Pré-requisito: `laya-serve` em `http://127.0.0.1:8000` (ou `LAYA_SERVE_URL`).

## PowerShell consumindo `--json`

Logs humanos vão para **stderr**; **stdout** é uma única linha JSON (ideal para `ConvertFrom-Json`).

> **PowerShell:** com `$ErrorActionPreference = 'Stop'`, texto em stderr do Python vira `NativeCommandError`. Nos scripts `*.ps1` do repo isso já é tratado (`Continue` só na chamada). Em one-liners manuais, use `$ErrorActionPreference = 'Continue'` em volta do `& python ...` ou redirecione `2>logs.txt`.

```powershell
$ErrorActionPreference = "Stop"
Set-Location C:\laya
$env:PYTHONIOENCODING = "utf-8"
$python = ".\.venv\Scripts\python.exe"

# Descobrir seletor (não clica)
$stderrFile = [System.IO.Path]::GetTempFileName()
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
try {
    $line = & $python examples\laya_find.py `
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
| **Arquivo padrão** | `examples/selector_cache.json` (ao lado de `laya_find.py`) |
| **Chave** | `host[:port]::intent normalizado` — mesmo host compartilha CTAs entre URLs |
| **Gravação** | Só seletores DOM verificados, estáveis (não voláteis), com `--use-cache` (padrão) |
| **Hit** | Revalida o seletor na página; se falhar, a entrada é removida automaticamente |

**Invalidar / forçar redescoberta**

- Uma execução: `--no-cache` (ignora leitura e **não grava**).
- Só esta combinação site+intent: apague a chave correspondente em `selector_cache.json`, ou delete o arquivo inteiro.
- Outro caminho: `--cache-path C:\caminho\outro_cache.json`.

Na 2ª visita bem-sucedida, espere `"cached": true` no JSON e tempo bem menor que a 1ª run.

## Limitações conhecidas

1. **Lotes grandes** — O torneio Laya processa candidatos em lotes (padrão `--batch-size 10`). Com dezenas/centenas de candidatos DOM, latência sobe e a escolha pode degradar; reduza ruído com `--policy strict` ou coleta mais focada (`--kind`).
2. **noul otimista** — A confirmação final (`confirm_noul`) pode marcar “atende o intent” com confiança alta em CTAs parecidos (ex.: Ajuda vs Cadastrar). Trate `confirm_noul < 0.5` como sinal de revisão manual; use `--no-confirm` só se você aceitar o risco.
3. **`none` pode errar** — Sem ranking, o torneio depende mais do acaso de embaralhamento e do tamanho do pool; útil para depuração, não como padrão em produção.
4. **Cache por host** — Intent igual em páginas diferentes do mesmo site pode reutilizar seletor inadequado; invalide o cache após redesign.
5. **Fora de escopo** — Cadeias fill/click/submit e login E2E não fazem parte do find; veja `docs/superpowers/plans/2026-09-26-laya-selector-discoverability.md`.

## Referências

- Índice exemplos: [README.md](README.md)
- CLI: `examples/laya_find.py` (`--help`) · [docs/selectors/cli.md](../docs/selectors/cli.md)
- Demos: [find_demo.ps1](find_demo.ps1), [hotmart_senha.ps1](hotmart_senha.ps1)
- Plano: [docs/superpowers/plans/2026-09-26-laya-selector-discoverability.md](../docs/superpowers/plans/2026-09-26-laya-selector-discoverability.md)
- Upstream Laya: https://github.com/NandhaKishorM/laya

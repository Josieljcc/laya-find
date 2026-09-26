# Contrato JSON (`--json`)

Stdout: **exatamente uma linha** JSON (sem logs).  
Stderr: progresso humano.

## Sucesso

```json
{
  "ok": true,
  "url": "https://exemplo.com/",
  "final_url": "https://exemplo.com/",
  "intent": "botão de login",
  "kind": "button",
  "selector": "a[href*=\"login\"]",
  "selector_ok": true,
  "matches": 5,
  "href": "https://accounts.exemplo.com/…",
  "text": "Login",
  "confidence": 0.55,
  "confirm_noul": 0.9,
  "policy": "strict",
  "cached": false
}
```

| Campo | Significado |
|-------|-------------|
| `ok` | Pipeline concluiu sem exceção fatal |
| `selector` | CSS (ou seletor Playwright) a usar no scraper |
| `selector_ok` | `querySelector` / Playwright achou ≥1 nó |
| `matches` | Quantidade de nós no momento da verificação |
| `href` / `text` | Observados (href pode ser volátil; use para debug) |
| `confidence` | Confiança do `choice` Laya (se houver) |
| `confirm_noul` | P(atende intent); `null` com `--no-confirm` ou hit de cache |
| `cached` | Resposta veio do cache revalidado |
| `policy` | Política usada |

## Falha

Ainda é uma linha JSON com `"ok": false` (args faltando, serve offline, zero candidatos, erro Playwright/Laya). Exit code ≠ 0. Detalhe em `text` e/ou stderr.

## Consumo PowerShell

Ver [../../examples/LAYA_FIND.md](../../examples/LAYA_FIND.md).

Implementação: `examples/laya_find_lib/contract.py` · testes: `tests/test_result_contract.py`.

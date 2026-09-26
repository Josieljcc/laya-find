# Desenvolvimento

Para agentes e humanos que alteram o código deste workspace.

## Princípios

- Find = **encontrabilidade**; scraper externo = **execução**.  
- Testes unitários cobrem funções puras em `src/laya_find` (sem browser).
- Smoke manual (Playwright + `laya-serve`) só quando a mudança afeta coleta/torneio real.  
- Commits apenas se o humano pedir.

## Preparação

O install editável é obrigatório antes de executar testes ou a CLI:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

## Layout de testes

```
tests/
  test_selectors.py
  test_result_contract.py
  test_policy.py
  test_cache.py
  test_normalize.py
  test_tournament_labels.py
  test_cli_behavior.py
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m pytest tests\test_selectors.py -v
```

Os testes importam o pacote instalado como `laya_find`.

## Como adicionar comportamento

| Mudança | Onde |
|---------|------|
| Nova regra de seletor estável | `src/laya_find/selectors.py` + teste |
| Nova política / narrow | `src/laya_find/policy.py` + teste |
| Campo no JSON | `src/laya_find/contract.py` + `test_result_contract.py` + docs |
| Pipeline de descoberta | `src/laya_find/find.py` + teste |
| Flag CLI | `src/laya_find/cli.py` + doc [selectors/cli.md](selectors/cli.md) |

## Smoke manual (opcional)

Com `laya-serve` em `:8000`:

```powershell
.\.venv\Scripts\laya-find.exe `
  --policy strict --url "https://www.eduzz.com/" --mode dom `
  --intent "botão de login" --json --settle-ms 3000 --no-cache
```

Espere `"selector"` estável (ex. `a[href*="login"]`) e `"selector_ok": true`.

## Planos

Implementação histórica da encontrabilidade:  
[superpowers/plans/2026-09-26-laya-selector-discoverability.md](superpowers/plans/2026-09-26-laya-selector-discoverability.md)

Scratch SDD (não é código de produto): `.superpowers/sdd/` — pode ignorar em reviews de produto.

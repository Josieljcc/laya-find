# Desenvolvimento

Para agentes e humanos que alteram o código deste workspace.

## Princípios

- Find = **encontrabilidade**; scraper externo = **execução**.  
- Testes unitários cobrem funções puras em `laya_find_lib` (sem browser).  
- Smoke manual (Playwright + `laya-serve`) só quando a mudança afeta coleta/torneio real.  
- Commits apenas se o humano pedir.

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

`pytest.ini` define `pythonpath = .` para imports `examples.laya_find_lib…`.

## Como adicionar comportamento

| Mudança | Onde |
|---------|------|
| Nova regra de seletor estável | `laya_find_lib/selectors.py` + teste |
| Nova política / narrow | `laya_find_lib/policy.py` + teste |
| Campo no JSON | `laya_find_lib/contract.py` + `test_result_contract.py` + docs |
| Flag CLI | `examples/laya_find.py` + doc [selectors/cli.md](selectors/cli.md) |

## Smoke manual (opcional)

Com `laya-serve` em `:8000`:

```powershell
.\.venv\Scripts\python.exe examples\laya_find.py `
  --policy strict --url "https://www.eduzz.com/" --mode dom `
  --intent "botão de login" --json --settle-ms 3000 --no-cache
```

Espere `"selector"` estável (ex. `a[href*="login"]`) e `"selector_ok": true`.

## Planos

Implementação histórica da encontrabilidade:  
[superpowers/plans/2026-09-26-laya-selector-discoverability.md](superpowers/plans/2026-09-26-laya-selector-discoverability.md)

Scratch SDD (não é código de produto): `.superpowers/sdd/` — pode ignorar em reviews de produto.

# AGENTS.md

Instruções curtas para agentes de código neste workspace. Detalhes ficam nos docs linkados — **leia o doc certo** em vez de inventar comportamento.

## Missão do repo

Descobrir **seletores DOM/network estáveis** via Playwright + Laya (`laya_find`), para um **scraper externo** consumir.  
**Não** implementar fill/click/submit/login E2E no caminho feliz do find (exceto `--reveal` opt-in documentado).

## Antes de mudar código

1. [docs/architecture.md](docs/architecture.md) — fluxo e módulos  
2. [docs/selectors/overview.md](docs/selectors/overview.md) — o que o find pode / não pode fazer  
3. Contrato JSON: [docs/selectors/json-contract.md](docs/selectors/json-contract.md)  
4. Políticas: [docs/selectors/policies.md](docs/selectors/policies.md)

## Comandos úteis

```powershell
# Testes
.\.venv\Scripts\python.exe -m pytest tests -q

# CLI (laya-serve em :8000)
.\.venv\Scripts\python.exe examples\laya_find.py --help
```

Setup completo: [docs/setup.md](docs/setup.md) · Dev: [docs/development.md](docs/development.md)

## Mapa de código

| Área | Onde |
|------|------|
| CLI | `examples/laya_find.py` |
| Lib | `examples/laya_find_lib/` (`selectors`, `policy`, `cache`, `contract`, `normalize`, `decide`) |
| Exemplos | `examples/README.md` |
| Integração scraper | `examples/LAYA_FIND.md` |
| Testes | `tests/` |
| Plano histórico | `docs/superpowers/plans/2026-09-26-laya-selector-discoverability.md` |

## Regras

- Manter stdout de `--json` = **uma** linha JSON; logs em stderr.  
- Preferir seletores estáveis (`#id`, `[name=…]`, `a[href*="login"]`) a URLs absolutas com UUID/query.  
- Cache em `examples/selector_cache.json` (gitignored) — não commitá-lo.  
- `laya_find_heuristic.py` é wrapper de `--policy strict`; mudanças de política vão em `laya_find_lib/policy.py`.  
- Não commitar secrets; credenciais só via env se algum exemplo de login for usado.  
- Commits só se o humano pedir.

## Índice humano

[README.md](README.md) · [docs/README.md](docs/README.md)

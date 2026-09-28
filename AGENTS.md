# AGENTS.md

Instruções curtas para agentes de código neste workspace. Detalhes ficam nos docs linkados — **leia o doc certo** em vez de inventar comportamento.

## Missão do repo

Descobrir **seletores DOM/network estáveis** via Playwright + Laya (`laya_find`), para um **scraper externo** consumir.  
**Não** implementar fill/click/submit automático no caminho feliz do find (exceto `--reveal` opt-in). Login **manual** headed fica em `laya-login` (mesma sessão Playwright → find).

## Antes de mudar código

1. [docs/architecture.md](docs/architecture.md) — fluxo e módulos  
2. [docs/selectors/overview.md](docs/selectors/overview.md) — o que o find pode / não pode fazer  
3. Contrato JSON: [docs/selectors/json-contract.md](docs/selectors/json-contract.md)  
4. Políticas: [docs/selectors/policies.md](docs/selectors/policies.md)

## Comandos úteis

Com venv ativo (Linux/macOS: `source .venv/bin/activate`; Windows: `.\.venv\Scripts\Activate.ps1`):

```bash
python -m pytest tests -q
laya-find --help
laya-login --help
```

Sem ativar: `.venv/bin/…` (Unix) ou `.venv\Scripts\….exe` (Windows).

Setup completo: [docs/setup.md](docs/setup.md) · Dev: [docs/development.md](docs/development.md)

## Mapa de código

| Área | Onde |
|------|------|
| CLI find | `src/laya_find/cli.py` (`laya-find`) |
| CLI login | `src/laya_find/login_cli.py` (`laya-login`) |
| Wizard login | `src/laya_find/login_flow.py` |
| Lib | `src/laya_find/` |
| Exemplos | `examples/` (demos only) |
| Integração scraper | `examples/LAYA_FIND.md` |
| Testes | `tests/` |
| Plano histórico | `docs/superpowers/plans/2026-09-26-laya-selector-discoverability.md` |

## Regras

- Manter stdout de `--json` = **uma** linha JSON; logs em stderr.  
- Preferir seletores estáveis (`#id`, `[name=…]`, `a[href*="login"]`) a URLs absolutas com UUID/query.  
- Cache padrão em `./selector_cache.json` (cwd, gitignored) — não commitá-lo.
- Mudanças de política vão em `src/laya_find/policy.py`; para política agressiva, use `--policy strict`.
- Não commitar secrets; credenciais só via env se algum exemplo de login for usado.  
- Commits só se o humano pedir.

## Índice humano

[README.md](README.md) · [docs/README.md](docs/README.md)

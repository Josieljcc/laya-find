# Laya Find — Selector Discoverability Improvements

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Tornar o `laya_find` um descobridor confiável de seletores estáveis para alimentar um scraper externo, resistindo a mudanças de página/BFF.

**Architecture:** Playwright coleta candidatos no DOM (e opcionalmente network); Laya escolhe o melhor match para um intent; a saída é um contrato JSON (`selector`, `href`, `confidence`, `url`) consumível pelo scraper existente. Heurísticas de ranking ficam como política opcional (`none|light|strict`), não como lógica espalhada. Cache de seletores por `(url_pattern, intent)` acelera revisitas e detecta quebra.

**Tech Stack:** Python 3.12, Playwright, `laya-serve` (HTTP `/v1/systemone`), JSON CLI.

**Integration guide:** [examples/LAYA_FIND.md](../../../examples/LAYA_FIND.md)

**Out of scope (explícito):** cadeias fill/click/submit, login automatizado end-to-end, substituição do scraper do usuário. Ações ficam para outro processo que já existe.

## Global Constraints

- Não acoplar fill/click ao caminho feliz do find.
- Preferir seletores CSS estáveis (`#id`, `[name=…]`, `a[href*="login"]`) a URLs absolutas voláteis (UUID, query longas).
- Manter `laya-serve` como backend de decisão (multilingual).
- Saída machine-readable obrigatória para integração (`--json` / arquivo).
- Backup da política agressiva já existe em `examples/laya_find_heuristic.py`; unificar em modos, não manter duas árvores divergentes para sempre.
- Commits só quando o usuário pedir.

---

## File map

| File | Responsibility |
|------|----------------|
| `examples/laya_find.py` | CLI única (modos de política + torneio + JSON) |
| `examples/laya_find_heuristic.py` | Deprecar após unificação (thin wrapper ou remoção) |
| `examples/laya_find_lib/selectors.py` | Geração/score de seletores estáveis (testável sem browser) |
| `examples/laya_find_lib/cache.py` | Cache `(site, intent) → selector` + validação |
| `examples/laya_find_lib/collect.py` | Extração DOM/network + dedupe |
| `examples/laya_find_lib/decide.py` | Chamadas Laya + torneio |
| `examples/selector_cache.json` | Cache local (gitignore) |
| `tests/test_selectors.py` | Unidade: estabilidade / volatilidade |
| `tests/test_cache.py` | Unidade: hit/miss/invalidate |
| `.gitignore` | Ignorar cache local |

---

### Task 1: Extrair geração de seletores estáveis para módulo testável

**Files:**
- Create: `examples/laya_find_lib/__init__.py`
- Create: `examples/laya_find_lib/selectors.py`
- Create: `tests/test_selectors.py`
- Modify: `examples/laya_find.py` (importar helpers Python de repair; JS buildSelector pode ficar no collect por enquanto)
- Modify: `examples/laya_find_heuristic.py` (mesmo import, evitar drift)

**Interfaces:**
- Produces:
  - `is_volatile_href(href: str) -> bool`
  - `is_volatile_selector(sel: str) -> bool`
  - `stable_href_candidates(href: str) -> list[str]` — ordenados do mais estável ao mais específico
  - `score_selector_stability(sel: str) -> int` — maior = melhor

- [ ] **Step 1: Write failing tests**

```python
# tests/test_selectors.py
from examples.laya_find_lib.selectors import (
    is_volatile_href,
    is_volatile_selector,
    stable_href_candidates,
    score_selector_stability,
)

VOLATILE = (
    "https://accounts.eduzz.com/53124931-1a7a-424b-aca7-a2eb91fd5b20/login"
    "?isPartnerCreate=true&redirectTo=https%3A%2F%2Forbita.eduzz.com%2F"
)

def test_volatile_href_detects_uuid_and_query():
    assert is_volatile_href(VOLATILE) is True
    assert is_volatile_href("https://dashboard.kiwify.com/login?lang=pt") is False

def test_stable_candidates_prefer_contains_login():
    cands = stable_href_candidates(VOLATILE)
    assert cands[0] == 'a[href*="login"]'
    assert any('href="' in c and "http" in c for c in cands)  # full URL last
    assert cands[-1].startswith('a[href="http')

def test_stability_scores_contains_above_full_url():
    assert score_selector_stability('a[href*="login"]') > score_selector_stability(
        f'a[href="{VOLATILE}"]'
    )
    assert is_volatile_selector(f'a[href="{VOLATILE}"]') is True
    assert is_volatile_selector('a[href*="login"]') is False
```

- [ ] **Step 2: Run tests — expect FAIL (module missing)**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_selectors.py -v
```

Expected: import error / FAIL

- [ ] **Step 3: Implement `examples/laya_find_lib/selectors.py`**

Move logic from `repair_selector` / `_volatile_*` / `_stable_href_candidates` into this module. Keep the same keyword list: `login`, `signin`, `signup`, `cadastro`, `register`, `auth`. Full absolute `href=` always last.

- [ ] **Step 4: Wire imports in both CLIs** so `repair_selector` chama `stable_href_candidates` / `is_volatile_selector`.

- [ ] **Step 5: Run tests — expect PASS**

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_selectors.py -v
```

- [ ] **Step 6: Manual smoke Eduzz**

```powershell
.\.venv\Scripts\python.exe examples\laya_find_heuristic.py --url "https://www.eduzz.com/" --mode dom --intent "botão de login" --action print --settle-ms 3000
```

Expected: `selector` like `a[href*="login"]`, not full UUID URL.

---

### Task 2: Contrato JSON para o scraper externo

**Files:**
- Modify: `examples/laya_find.py`
- Modify: `examples/laya_find_heuristic.py` (ou só a CLI unificada se Task 3 já existir)
- Create: `tests/test_result_contract.py`

**Interfaces:**
- Produces dataclass / dict:

```python
{
  "ok": true,
  "url": "https://…",
  "final_url": "https://…",   # após redirects/reveal
  "intent": "botão de login",
  "kind": "button",
  "selector": "a[href*=\"login\"]",
  "selector_ok": true,
  "matches": 5,
  "href": "https://…",         # href observado (pode ser volátil; só informativo)
  "text": "Login",
  "confidence": 0.33,          # answer_confidence do choice, se houver
  "confirm_noul": 0.95,
  "policy": "light",
  "cached": false
}
```

- Consumes: resultado atual do torneio + `verify_selector`

- [ ] **Step 1: Write contract test**

```python
def test_result_has_required_keys():
    from examples.laya_find_lib.contract import build_result
    r = build_result(
        url="https://x",
        final_url="https://x",
        intent="login",
        kind="button",
        selector='a[href*="login"]',
        selector_ok=True,
        matches=2,
        href="https://x/login",
        text="Login",
        confidence=0.5,
        confirm_noul=0.9,
        policy="light",
        cached=False,
    )
    assert r["ok"] is True
    assert set(r) >= {
        "ok", "url", "intent", "kind", "selector", "selector_ok", "matches", "policy"
    }
```

- [ ] **Step 2: Implement `examples/laya_find_lib/contract.py` + flag `--json`**

Quando `--json`: imprimir **somente** uma linha JSON em stdout (logs humanos em stderr). Isso permite:

```powershell
$result = .\.venv\Scripts\python.exe examples\laya_find.py ... --json | ConvertFrom-Json
# scraper usa $result.selector
```

- [ ] **Step 3: Document one-liner no docstring do CLI**

---

### Task 3: Unificar políticas `none|light|strict` numa CLI só

**Files:**
- Modify: `examples/laya_find.py`
- Modify: `examples/laya_find_heuristic.py` → wrapper deprecado que chama `laya_find.py --policy strict`
- Create: `examples/laya_find_lib/policy.py`

**Interfaces:**
- `apply_policy(cands, intent, policy: Literal["none","light","strict"]) -> list[Candidate]`
  - `none`: só dedupe (versão “Laya decide”)
  - `light`: dedupe + drop `<summary>` já na coleta + soft boost por overlap de tokens (sem hard-narrow)
  - `strict`: comportamento atual do heuristic (narrow por frase/senha/login)

- [ ] **Step 1: Port `narrow_by_intent` / `soft_rank` / `intent_tokens` from heuristic into `policy.py`**

- [ ] **Step 2: Add `--policy` default `light`**

- [ ] **Step 3: Make `laya_find_heuristic.py` a 10-line wrapper**

```python
"""Deprecated: use laya_find.py --policy strict"""
import sys
from examples.laya_find import main
sys.argv = [sys.argv[0], "--policy", "strict", *sys.argv[1:]]
raise SystemExit(main())
```

(Adjust import path if running as script — prefer subprocess or refactor `main` to accept argv only, already true.)

- [ ] **Step 4: Regression smoke**

```powershell
# strict: Kiwify cadastrar
.\.venv\Scripts\python.exe examples\laya_find.py --policy strict --url "https://kiwify.com.br/" --mode dom --intent "botão cadastrar agora" --action print --settle-ms 3000 --json

# none: same URL (document expected flakiness; only checks JSON shape + selector_ok field present)
```

---

### Task 4: Cache de seletores por site + intent

**Files:**
- Create: `examples/laya_find_lib/cache.py`
- Create: `tests/test_cache.py`
- Modify: `examples/laya_find.py` (lookup antes do torneio; save depois)
- Modify: `.gitignore` — add `examples/selector_cache.json`
- Create: default path `examples/selector_cache.json` (não commitado)

**Interfaces:**
- `cache_key(url: str, intent: str) -> str` — host + path prefix + normalized intent
- `CacheStore.load(path) / save / get(key) / put(key, record)`
- Record: `{selector, kind, href_hint, updated_at, hits, last_ok}`

**Flow:**
1. Se `--use-cache` (default on) e hit: `verify_selector` na página atual.
2. Se `selector_ok` e `matches >= 1`: retornar imediatamente (`cached: true`).
3. Senão: invalidar entrada, rodar discover completo, gravar novo seletor **estável** (não gravar URL UUID completa se existir alternativa `href*=`).

- [ ] **Step 1: Unit tests for key normalization and invalidate**

```python
def test_same_host_login_paths_share_or_split_as_designed():
    # Decide and document: key = netloc + intent only (broader reuse)
    # OR netloc + path_template. Prefer netloc + intent for CTAs on marketing pages.
    from examples.laya_find_lib.cache import cache_key
    a = cache_key("https://www.eduzz.com/", "botão de login")
    b = cache_key("https://www.eduzz.com/pricing", "botão de login")
    assert a == b  # marketing CTAs often shared in header
```

- [ ] **Step 2: Implement store + CLI flags `--use-cache/--no-cache/--cache-path`**

- [ ] **Step 3: Manual test**

```powershell
# 1st run: cached=false, writes cache
# 2nd run: cached=true, faster, same selector
.\.venv\Scripts\python.exe examples\laya_find.py --policy strict --url "https://www.eduzz.com/" --mode dom --intent "botão de login" --json --settle-ms 3000
.\.venv\Scripts\python.exe examples\laya_find.py --policy strict --url "https://www.eduzz.com/" --mode dom --intent "botão de login" --json --settle-ms 1000
```

---

### Task 5: Torneio mais justo para o Laya (sem voltar keyword soup)

**Files:**
- Modify: `examples/laya_find_lib/decide.py` (extract from CLI) or inline in `laya_find.py`
- Create: `tests/test_tournament_labels.py`

**Problem observed:** com `policy=none`, Laya escolheu Contato/mailto em vez de “Cadastrar agora”; noul ainda deu ~1.0.

**Changes:**
1. Labels curtas no `criteria`: `text="Cadastrar agora" | href*="signup"` (não dump longo).
2. Após vencedor, se `confirm_noul < 0.5` **ou** `confidence < 0.25`: segunda passagem só com candidatos cujo `text/href` contém algum token do intent (fallback único, documentado).
3. Deduplicar por destino normalizado: strip query + drop UUID path segments before tournament.

- [ ] **Step 1: Test label builder**

```python
def test_short_label_includes_text_and_stable_href_hint():
    from examples.laya_find_lib.decide import short_label
    label = short_label(
        text="Cadastrar agora",
        href="https://dashboard.kiwify.com/signup?lang=pt&country=br",
        kind="link",
    )
    assert "Cadastrar agora" in label
    assert "signup" in label.lower()
    assert "lang=pt" not in label  # no volatile query noise in label
```

- [ ] **Step 2: Implement short labels + low-confidence retry**

- [ ] **Step 3: Compare none vs strict on Kiwify cadastrar (manual table in PR/notes)**

---

### Task 6: Normalização de destino + dedupe por “mesmo lugar”

**Files:**
- Create: `examples/laya_find_lib/normalize.py`
- Create: `tests/test_normalize.py`
- Modify: collect/dedupe path

**Why:** Eduzz Login e “Começar gratuitamente” → mesmo destino; Kiwify tem 13 clones “Cadastrar agora”. O scraper precisa de **um** seletor estável, não 13 candidatas.

- [ ] **Step 1: `canonical_destination(href) -> str`**

```python
def test_strips_uuid_and_tracking_query():
    from examples.laya_find_lib.normalize import canonical_destination
    a = canonical_destination(
        "https://accounts.eduzz.com/53124931-1a7a-424b-aca7-a2eb91fd5b20/login?redirectTo=x&logo=y"
    )
    b = canonical_destination(
        "https://accounts.eduzz.com/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/login?foo=1"
    )
    assert a == b == "https://accounts.eduzz.com/login"
```

- [ ] **Step 2: Dedupe candidates by `canonical_destination` + kind, keep richest text label**

- [ ] **Step 3: Ensure JSON `href` still exposes one observed raw href for debugging**

---

### Task 7: Doc de integração com o scraper existente

**Files:**
- Create: `docs/superpowers/specs/2026-09-26-laya-selector-discovery.md` (curto)
- Or section in `examples/README.md` if preferred — use `examples/LAYA_FIND.md`

**Content (must include):**
1. Papel: **só encontrabilidade** → devolve seletor; o scraper do usuário executa.
2. Exemplo PowerShell consumindo `--json`.
3. Quando usar `--policy strict` vs `light` vs `none`.
4. Cache: onde fica, como invalidar (`--no-cache` ou apagar JSON).
5. Limitações conhecidas (Laya fraco em lotes grandes; noul pode ser otimista).

- [ ] **Step 1: Write `examples/LAYA_FIND.md`**
- [ ] **Step 2: Link from plan header / docstring**

---

## Suggested order

1 → 2 → 3 → 4 → 6 → 5 → 7

(Tasks 5 and 6 can swap; 6 helps 5.)

## Success metrics

| Scenario | Pass criteria |
|----------|----------------|
| Eduzz login CTA | Seletor estável `href*=` sem UUID; `selector_ok=true` em 2 loads |
| Kiwify “cadastrar agora” + `strict` | Seletor aponta signup; JSON consumível |
| Kiwify login email field | `#email` or `[name=email]` |
| 2ª visita Eduzz com cache | `cached=true`, tempo << 1ª run |
| Scraper integration | Lê `.selector` do JSON sem parse de logs |

## Non-goals reminder

- Não implementar wizards de fill/click neste plano.
- Não substituir o scraper atual; apenas melhorar a descoberta de seletores que ele consome.

---

## Self-review

- Spec coverage: encontrabilidade, estabilidade, cache, unificação de políticas, contrato JSON, doc de integração — cobertos. Ações — excluídas de propósito.
- Placeholders: nenhum TBD.
- Consistência: `policy` values `none|light|strict`; JSON keys estáveis na Task 2.

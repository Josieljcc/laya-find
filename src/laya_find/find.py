"""Localizador genérico: intent → tipo → coleta → política → torneio Laya.

Políticas:
  none: apenas dedupe; Laya decide em torneio embaralhado
  light: dedupe + soft-rank por tokens (padrão)
  strict: narrow e ranking agressivos (compatível com o script antigo)

Fluxo:
  1) Classifica o intent (heurística clara ou Laya) → kind
  2) Playwright coleta esse tipo (button também inclui <a> CTA)
  3) Torneio em lotes embaralhados até 1 vencedor (Laya em cada lote)
  4) noul: confirma se atende o intent

Requer laya-serve em http://127.0.0.1:8000 (ou LAYA_SERVE_URL).

Integração com scraper externo: examples/LAYA_FIND.md

Scraper: use ``FindOptions`` + ``run``; JSON vai para stdout e logs para stderr.
"""

from __future__ import annotations

import json
import random
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

from laya_find.cache import CacheStore, cache_key
from laya_find.contract import build_result, emit_json_line, summary_field
from laya_find.decide import (
    candidates_overlapping_intent,
    short_label,
)
from laya_find.normalize import dedupe_by_destination
from laya_find.policy import apply_policy
from laya_find.selectors import (
    is_volatile_selector,
    stable_href_candidates,
)

DEFAULT_SERVE = "http://127.0.0.1:8000"
DEFAULT_BATCH = 10
DEFAULT_CACHE_PATH = "selector_cache.json"
KIND_OPTIONS = ("input", "button", "link", "select", "network")


@dataclass
class FindOptions:
    url: str = ""
    intent: str = ""
    mode: str = ""
    kind: str = ""
    serve: str = DEFAULT_SERVE
    headed: bool = False
    listen_seconds: float = 5.0
    settle_ms: int = 1500
    timeout_ms: int = 30000
    batch_size: int = DEFAULT_BATCH
    policy: str = "light"
    no_tournament: bool = False
    no_confirm: bool = False
    reveal: bool = False
    use_cache: bool = True
    cache_path: str = DEFAULT_CACHE_PATH
    json_stdout: bool = False


@dataclass
class Candidate:
    key: str
    source: str  # dom | network
    kind: str
    summary: str
    selector: str = ""
    href: str = ""
    request: dict = field(default_factory=dict)


def _reconfigure_stdout() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8", errors="replace")


def check_serve(serve_url: str) -> dict:
    with urllib.request.urlopen(f"{serve_url.rstrip('/')}/health", timeout=5) as resp:
        return json.loads(resp.read().decode("utf-8"))


def laya_request(serve_url: str, state: str, questions: dict) -> tuple[dict, float]:
    payload = json.dumps(
        {
            "state": {"body": state},
            "questions": questions,
            "model": "multilingual",
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{serve_url.rstrip('/')}/v1/systemone",
        data=payload,
        headers={"content-type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body, (time.perf_counter() - t0) * 1000


def heuristic_kind(intent: str, mode: str) -> str | None:
    """High-confidence keyword map; None = ask Laya."""
    t = intent.lower()
    if mode == "network":
        return "network"
    if any(w in t for w in ("request", "xhr", "fetch", "api", "endpoint", "requisição", "requisicao")):
        return "network" if mode in ("network", "both") else None
    if any(w in t for w in ("senha", "password", "passwd", "email", "e-mail", "usuário", "usuario", "user", "campo", "input", "texto", "search", "busca", "pesquis")):
        if any(w in t for w in ("botão", "botao", "button", "clicar", "click")):
            return None
        return "input"
    if any(w in t for w in ("botão", "botao", "button", "submit", "entrar", "enviar", "salvar", "save", "acessar")):
        return "button"
    if any(w in t for w in ("dropdown", "select", "combo", "lista suspensa")):
        return "select"
    if any(w in t for w in ("link", "âncora", "ancora", "href", "menu")):
        return "link"
    return None


def classify_intent(intent: str, mode: str, serve_url: str) -> tuple[str, float]:
    """Resolve component kind: heuristic first, else Laya."""
    prior = heuristic_kind(intent, mode)
    if prior:
        return prior, 0.0

    if mode == "network":
        return "network", 0.0

    criteria = {
        "input": (
            "Caixa de texto / email / senha / busca / textarea. "
            "Use for password, login field, search box, form text fields."
        ),
        "button": (
            "Botão clicável ou submit. "
            "Use for Entrar, Login, Salvar, Enviar, Continuar."
        ),
        "link": (
            "Link de navegação (âncora a href). "
            "Use for menus and go-to-page links, not form submit."
        ),
        "select": (
            "Lista suspensa / dropdown / combobox. "
            "Only when the user wants a select/dropdown, not a text field."
        ),
    }
    if mode == "both":
        criteria["network"] = (
            "Requisição HTTP XHR/fetch/API, não um controle visual."
        )

    state = (
        f"Intenção do usuário: {intent}\n"
        "Escolha EXATAMENTE um tipo de componente para buscar na página."
    )
    questions = {
        "component_kind": {
            "type": "choice",
            "instructions": (
                "Qual tipo de componente a intenção pede? "
                "campo/senha/email/texto => input. "
                "botão/entrar/salvar/enviar => button. "
                "link/menu/href => link. "
                "dropdown/select => select. "
                "api/request/xhr => network. "
                "NÃO escolha select a menos que a intenção cite lista/dropdown."
            ),
            "criteria": criteria,
        }
    }
    result, ms = laya_request(serve_url, state, questions)
    kind = result["answers"]["component_kind"]["choice"]
    conf = result["answers"]["component_kind"].get("answer_confidence")
    print(f"  laya kind raw={kind} conf={conf}")
    if kind not in KIND_OPTIONS:
        kind = "input"
    if mode == "dom" and kind == "network":
        kind = "input"
    return kind, ms


def extract_dom(page, kinds: set[str] | None = None) -> list[Candidate]:
    """Collect interactive DOM controls (main frame + same-origin iframes)."""
    kinds = kinds or {"input", "button", "link", "select"}
    script = """(kinds) => {
      const want = new Set(kinds);
      const out = [];
      const cssEscape = (s) => {
        if (window.CSS && CSS.escape) return CSS.escape(s);
        return String(s).replace(/[^a-zA-Z0-9_-]/g, '\\\\$&');
      };
      const q = (s) => String(s || '').replace(/\\\\/g, '\\\\\\\\').replace(/"/g, '\\\\"');

      const uniqueMatch = (sel, el, root) => {
        try {
          const nodes = root.querySelectorAll(sel);
          if (nodes.length === 1 && nodes[0] === el) return true;
          if (nodes.length >= 1 && [...nodes].includes(el)) return nodes.length;
        } catch (e) { return false; }
        return false;
      };

      const buildSelector = (el, kind, root) => {
        const tag = el.tagName.toLowerCase();
        const type = (el.getAttribute('type') || '').toLowerCase();
        const id = el.id || '';
        const name = el.getAttribute('name') || '';
        const placeholder = el.getAttribute('placeholder') || '';
        const aria = el.getAttribute('aria-label') || '';
        const hrefAttr = el.getAttribute('href') || '';
        const role = el.getAttribute('role') || '';
        const dataTest = el.getAttribute('data-testid') || el.getAttribute('data-test') || '';
        const candidates = [];

        // Higher = more stable across BFF/SPA reloads (avoid full URLs with UUID/query).
        const stability = (sel) => {
          if (!sel) return 0;
          if (sel.startsWith('#')) return 100;
          if (sel.includes('[data-testid') || sel.includes('[data-test')) return 95;
          if (sel.includes('[name="') && sel.includes('[type="')) return 92;
          if (sel.includes('[name="')) return 88;
          if (/href\\*="(login|signin|sign-in|signup|sign-up|cadastro|register|auth)"/i.test(sel)) return 90;
          if (/href\\*="[^"]{1,48}"/.test(sel) && !/https?:/.test(sel)) return 82;
          if (sel.includes('[href*=')) return 75;
          if (sel.includes('[aria-label=')) return 70;
          if (sel.includes('[placeholder=')) return 68;
          // Full absolute / long href= is brittle (UUID, redirectTo, logos…)
          if (/\\[href="https?:/.test(sel)) return 8;
          if (/\\[href="/.test(sel) && sel.length > 60) return 12;
          if (/\\[href="/.test(sel)) return 40;
          return 30;
        };

        const isVolatileHref = (h) => {
          if (!h) return false;
          return /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-/i.test(h)
            || h.length > 100
            || (h.includes('?') && h.split('?')[1].length > 30)
            || /[?&](token|session|sid|redirect|redirectTo|logo|initial_)/i.test(h);
        };

        if (id) candidates.push(`#${cssEscape(id)}`);
        if (dataTest) candidates.push(`[data-testid="${q(dataTest)}"]`);

        // Links: stable contains-selectors first; full href= only as last resort.
        if (hrefAttr) {
          const keywords = ['login', 'signin', 'sign-in', 'signup', 'sign-up', 'cadastro', 'register', 'auth', 'entrar', 'conta'];
          const low = hrefAttr.toLowerCase();
          for (const kw of keywords) {
            if (low.includes(kw)) candidates.push(`${tag}[href*="${kw}"]`);
          }
          try {
            const abs = new URL(hrefAttr, location.href);
            // Host without volatile path, e.g. a[href*="accounts.eduzz.com"]
            if (abs.hostname && abs.hostname !== location.hostname) {
              candidates.push(`${tag}[href*="${q(abs.hostname)}"]`);
            }
            // Stable path segments (skip UUID-looking parts)
            const segs = abs.pathname.split('/').filter(Boolean);
            for (const seg of segs) {
              if (seg.length < 3 || seg.length > 40) continue;
              if (/^[0-9a-f-]{20,}$/i.test(seg)) continue;
              if (keywords.some(k => seg.toLowerCase().includes(k))) {
                candidates.push(`${tag}[href*="/${q(seg)}"]`);
                candidates.push(`${tag}[href*="${q(seg)}"]`);
              }
            }
            if (!isVolatileHref(hrefAttr)) {
              const pathOnly = abs.pathname;
              if (pathOnly && pathOnly !== '/') {
                candidates.push(`${tag}[href*="${q(pathOnly)}"]`);
                candidates.push(`${tag}[href="${q(pathOnly)}"]`);
              }
              candidates.push(`${tag}[href="${q(hrefAttr)}"]`);
            } else {
              // Volatile: still keep full href as absolute last resort
              candidates.push(`${tag}[href="${q(hrefAttr)}"]`);
            }
          } catch (e) {
            candidates.push(`${tag}[href="${q(hrefAttr)}"]`);
          }
        }

        if (name) candidates.push(`${tag}[name="${q(name)}"]`);
        if (type && name) candidates.push(`${tag}[type="${q(type)}"][name="${q(name)}"]`);
        if (type) candidates.push(`${tag}[type="${q(type)}"]`);
        if (aria) candidates.push(`${tag}[aria-label="${q(aria)}"]`);
        if (placeholder) candidates.push(`${tag}[placeholder="${q(placeholder)}"]`);
        if (role) candidates.push(`${tag}[role="${q(role)}"]`);

        // Score: stability first, then fewer matches. Accept up to 8 matches for stable sels.
        let best = '';
        let bestScore = -Infinity;
        for (const sel of [...new Set(candidates)]) {
          const n = uniqueMatch(sel, el, root);
          if (!n) continue;
          const count = n === true ? 1 : n;
          const stab = stability(sel);
          const maxOk = stab >= 75 ? 8 : (stab >= 40 ? 3 : 1);
          if (count > maxOk) continue;
          // Prefer stable; among equals prefer fewer matches
          const score = stab * 100 - count;
          if (score > bestScore) {
            bestScore = score;
            best = sel;
          }
        }
        if (best) return best;

        // Structural fallback: short path with nth-of-type (valid CSS)
        const parts = [];
        let cur = el;
        for (let depth = 0; cur && cur.nodeType === 1 && depth < 5; depth++) {
          const t = cur.tagName.toLowerCase();
          const parent = cur.parentElement;
          if (!parent) { parts.unshift(t); break; }
          const siblings = [...parent.children].filter(c => c.tagName === cur.tagName);
          if (siblings.length === 1) parts.unshift(t);
          else parts.unshift(`${t}:nth-of-type(${siblings.indexOf(cur) + 1})`);
          cur = parent;
          const trial = parts.join(' > ');
          if (uniqueMatch(trial, el, root) === true) return trial;
        }
        return parts.join(' > ') || tag;
      };

      const push = (el, kind, frameHint, root) => {
        const tag = el.tagName.toLowerCase();
        const type = (el.getAttribute('type') || '').toLowerCase();
        if (kind === 'input' && ['hidden', 'checkbox', 'radio', 'file', 'image', 'reset', 'color', 'range'].includes(type)) return;
        const id = el.id || '';
        const name = el.getAttribute('name') || '';
        const placeholder = el.getAttribute('placeholder') || '';
        const aria = el.getAttribute('aria-label') || '';
        const autocomplete = el.getAttribute('autocomplete') || '';
        const role = el.getAttribute('role') || '';
        const href = el.getAttribute('href') || '';
        const text = (el.innerText || el.value || '').trim().slice(0, 100);
        let label = '';
        if (id) {
          const lab = root.querySelector(`label[for="${cssEscape(id)}"]`);
          if (lab) label = (lab.innerText || '').trim().slice(0, 100);
        }
        if (!label) {
          const parentLab = el.closest('label');
          if (parentLab) label = (parentLab.innerText || '').trim().slice(0, 100);
        }
        if (kind === 'button' && type !== 'submit' && !id && !text && !aria && !name) return;
        if (kind === 'link' && !text && !aria && !href) return;

        const selector = buildSelector(el, kind, root);
        out.push({ kind, tag, type, id, name, placeholder, aria, autocomplete, role, href, label, text, selector, frame: frameHint || '' });
      };

      const scan = (root, frameHint) => {
        const doc = root.documentElement ? root : (root.ownerDocument || document);
        const scope = root.querySelectorAll ? root : doc;
        if (want.has('input')) {
          scope.querySelectorAll('input:not([type="hidden"]), textarea').forEach(el => push(el, 'input', frameHint, doc));
        }
        if (want.has('select')) {
          scope.querySelectorAll('select').forEach(el => push(el, 'select', frameHint, doc));
        }
        if (want.has('button')) {
          scope.querySelectorAll('button, input[type="submit"], input[type="button"], [role="button"]').forEach(el => {
            // FAQ <summary role=button> pollutes CTA search — skip unless explicitly wanted
            if (el.tagName && el.tagName.toLowerCase() === 'summary') return;
            push(el, 'button', frameHint, doc);
          });
        }
        if (want.has('link')) {
          scope.querySelectorAll('a[href]').forEach(el => {
            const t = (el.innerText || '').trim();
            const aria = el.getAttribute('aria-label') || '';
            if (t || aria) push(el, 'link', frameHint, doc);
          });
        }
      };

      scan(document, '');
      return out;
    }"""

    raw = page.evaluate(script, list(kinds))

    # Same-origin iframes (cross-origin will throw; ignore)
    for i, frame in enumerate(page.frames):
        if frame == page.main_frame:
            continue
        try:
            extra = frame.evaluate(script, list(kinds))
            for item in extra:
                item["frame"] = item.get("frame") or f"iframe_{i}"
            raw.extend(extra)
        except Exception:
            continue

    cands: list[Candidate] = []
    for i, item in enumerate(raw, 1):
        key = f"dom_{i}"
        bits = [f"kind={item['kind']}", f"tag={item['tag']}"]
        for attr in ("type", "id", "name", "placeholder", "label", "aria", "autocomplete", "role", "text", "href", "frame"):
            if item.get(attr):
                label = "aria-label" if attr == "aria" else attr
                bits.append(f"{label}={item[attr]}")
        cands.append(
            Candidate(
                key=key,
                source="dom",
                kind=item["kind"],
                summary=f"{key}: " + ", ".join(bits),
                selector=item.get("selector") or "",
                href=item.get("href") or "",
            )
        )
    return cands


def repair_selector(page, chosen: Candidate) -> Candidate:
    """Ensure selector is valid CSS; prefer stable href*= over volatile full URLs."""
    ok, count = verify_selector(page, chosen.selector)
    if ok and count >= 1 and not is_volatile_selector(chosen.selector):
        return chosen

    href = chosen.href
    if not href and "href=" in chosen.summary:
        try:
            href = chosen.summary.split("href=", 1)[1].split(",", 1)[0].strip()
        except Exception:
            href = ""
    if href:
        for sel in stable_href_candidates(href):
            ok, count = verify_selector(page, sel)
            if ok and count >= 1:
                chosen.selector = sel
                return chosen
    return chosen


def verify_selector(page, selector: str, frame_hint: str = "") -> tuple[bool, int]:
    """Check selector resolves in the page (CSS / Playwright). Returns (ok, count)."""
    if not selector:
        return False, 0
    try:
        # Prefer main document querySelector for CSS selectors
        if not selector.startswith("text=") and not selector.startswith("xpath="):
            count = page.evaluate(
                """(sel) => {
                  try { return document.querySelectorAll(sel).length; }
                  catch (e) { return -1; }
                }""",
                selector,
            )
            if isinstance(count, int) and count > 0:
                return True, count
            # Try iframes
            for frame in page.frames:
                if frame == page.main_frame:
                    continue
                try:
                    count = frame.evaluate(
                        """(sel) => {
                          try { return document.querySelectorAll(sel).length; }
                          catch (e) { return -1; }
                        }""",
                        selector,
                    )
                    if isinstance(count, int) and count > 0:
                        return True, count
                except Exception:
                    continue
        loc = page.locator(selector)
        n = loc.count()
        return n > 0, n
    except Exception:
        return False, 0


def resolve_cache_hit(
    store: CacheStore, key: str, page
) -> tuple[dict, int] | None:
    """Verify a cached selector, updating hits or removing stale entries."""
    record = store.get(key)
    if not record:
        return None
    selector = str(record.get("selector") or "")
    ok, matches = verify_selector(page, selector)
    if not ok or matches < 1:
        store.invalidate(key)
        store.save()
        return None
    record["hits"] = int(record.get("hits") or 0) + 1
    record["last_ok"] = True
    store.put(key, record)
    store.save()
    return record, matches


def save_cache_candidate(
    store: CacheStore,
    key: str,
    chosen: Candidate,
    selector_ok: bool,
    matches: int,
) -> bool:
    """Persist only selectors that are verified and stable enough to reuse."""
    if (
        chosen.source != "dom"
        or not chosen.selector
        or not selector_ok
        or matches < 1
        or is_volatile_selector(chosen.selector)
    ):
        return False
    store.put(
        key,
        {
            "selector": chosen.selector,
            "kind": chosen.kind,
            "href_hint": chosen.href or summary_field(chosen.summary, "href"),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "hits": 0,
            "last_ok": True,
        },
    )
    store.save()
    return True


def try_reveal_login_ui(page) -> None:
    """Best-effort: click common 'Entrar/Login' triggers so password fields appear."""
    selectors = [
        "text=/^(entrar|login|acessar|sign in|fazer login)$/i",
        "a:has-text('Entrar')",
        "button:has-text('Entrar')",
        "a:has-text('Login')",
        "button:has-text('Login')",
        "[data-testid*='login' i]",
        "[href*='login' i]",
    ]
    for sel in selectors:
        try:
            loc = page.locator(sel).first
            if loc.count() == 0:
                continue
            if not loc.is_visible(timeout=500):
                continue
            loc.click(timeout=1500)
            page.wait_for_timeout(800)
            return
        except Exception:
            continue


def settle_page(page, settle_ms: int, kind: str, *, reveal: bool = False) -> None:
    try:
        page.wait_for_load_state("networkidle", timeout=min(settle_ms, 10000))
    except Exception:
        pass
    page.wait_for_timeout(max(settle_ms, 300))
    if reveal and kind == "input":
        # Password fields often live behind a login CTA on marketing pages
        before = len(page.query_selector_all("input[type='password']"))
        if before == 0:
            print("nenhum input[type=password] ainda — tentando revelar UI de login …")
            try_reveal_login_ui(page)
            page.wait_for_timeout(1000)


def capture_network(page, listen_seconds: float, attach_only: bool = False):
    seen: list[dict] = []

    def on_request(req) -> None:
        try:
            rtype = req.resource_type
            if rtype not in ("xhr", "fetch", "document"):
                return
            url = req.url
            if rtype == "document" and any(
                url.lower().endswith(ext) for ext in (".css", ".js", ".png", ".jpg", ".svg", ".woff2")
            ):
                return
            post = ""
            try:
                post = (req.post_data or "")[:240]
            except Exception:
                post = ""
            seen.append(
                {
                    "method": req.method,
                    "url": url[:300],
                    "resource_type": rtype,
                    "post_data": post,
                }
            )
        except Exception:
            return

    def detach() -> None:
        try:
            page.remove_listener("request", on_request)
        except Exception:
            pass

    def to_candidates() -> list[Candidate]:
        uniq: dict[str, dict] = {}
        for item in seen:
            uniq[f"{item['method']} {item['url']}"] = item
        cands: list[Candidate] = []
        for i, item in enumerate(uniq.values(), 1):
            key = f"net_{i}"
            bits = [
                f"method={item['method']}",
                f"type={item['resource_type']}",
                f"url={item['url']}",
            ]
            if item.get("post_data"):
                bits.append(f"body={item['post_data']}")
            cands.append(
                Candidate(
                    key=key,
                    source="network",
                    kind="network",
                    summary=f"{key}: " + ", ".join(bits),
                    request=item,
                )
            )
        return cands

    page.on("request", on_request)
    if attach_only:
        return seen, detach, to_candidates
    page.wait_for_timeout(int(listen_seconds * 1000))
    detach()
    return to_candidates()


def collection_kinds(kind: str) -> set[str]:
    """DOM kinds to scrape for a classified intent kind.

    Sites often style <a> as a 'button' (login CTAs). When the user asks for a
    botão/button, also collect links so semantic mismatch does not hide the target.
    """
    if kind == "button":
        return {"button", "link"}
    if kind == "link":
        return {"link", "button"}
    return {kind}


def cache_lookup_allowed(mode: str, kind: str) -> bool:
    """DOM selector cache cannot satisfy network discovery."""
    return mode in ("dom", "both") and kind != "network"


def choose_one(
    cands: list[Candidate],
    intent: str,
    serve_url: str,
    page_url: str,
    title: str,
    round_label: str,
) -> tuple[Candidate, float, float | None]:
    if len(cands) == 1:
        print(f"  {round_label}: único candidato {cands[0].key} (skip Laya)")
        return cands[0], 0.0, 1.0

    # Keep criteria focused on user-visible text and a stable URL path hint.
    criteria = {}
    for c in cands:
        text = (
            summary_field(c.summary, "text")
            or summary_field(c.summary, "label")
            or summary_field(c.summary, "aria-label")
            or summary_field(c.summary, "placeholder")
        )
        href = c.href or summary_field(c.summary, "href")
        criteria[c.key] = short_label(text, href, c.kind)

    state = "\n".join(
        [
            f"Page URL: {page_url}",
            f"Page title: {title}",
            f"User intent (match this exactly): {intent}",
            "Pick the single control whose visible text, label, or href "
            "best matches the intent. Prefer exact phrase matches "
            "(e.g. intent 'cadastrar agora' → text=Cadastrar agora). "
            "Do NOT pick unrelated nav items (Ajuda, FAQ, Menu) unless the intent asks for them.",
            f"Round: {round_label}",
        ]
    )
    questions = {
        "best_match": {
            "type": "choice",
            "instructions": (
                "Which candidate BEST matches the user intent? "
                f"Intent: {intent}. "
                "Match on text/label/href content, not on generic 'button-ness'."
            ),
            "criteria": criteria,
        }
    }
    result, ms = laya_request(serve_url, state, questions)
    key = result["answers"]["best_match"]["choice"]
    conf = result["answers"]["best_match"].get("answer_confidence")
    chosen = by_key(cands, key)
    print(f"  {round_label}: {chosen.key} ({ms:.0f} ms, conf={conf})")
    return chosen, ms, conf


def tournament(
    cands: list[Candidate],
    intent: str,
    serve_url: str,
    page_url: str,
    title: str,
    batch_size: int,
    shuffle_pool: bool = True,
) -> tuple[Candidate, float, float | None]:
    """Elimination rounds until one winner remains.

    Batches are shuffled (no keyword soft-rank) so Laya is the decision maker.
    """
    pool = list(cands)
    if shuffle_pool:
        random.shuffle(pool)
    total_ms = 0.0
    last_conf: float | None = None
    if len(pool) == 1:
        print(f"  único candidato {pool[0].key} (skip torneio)")
        return pool[0], 0.0, 1.0

    round_i = 1
    while len(pool) > 1:
        if len(pool) <= batch_size:
            winner, ms, last_conf = choose_one(
                pool, intent, serve_url, page_url, title, f"final(r{round_i},n={len(pool)})"
            )
            return winner, total_ms + ms, last_conf

        winners: list[Candidate] = []
        batches = [pool[i : i + batch_size] for i in range(0, len(pool), batch_size)]
        print(f"fase {round_i}: {len(pool)} candidatos → {len(batches)} lotes de ≤{batch_size}")
        for bi, batch in enumerate(batches, 1):
            w, ms, _ = choose_one(
                batch,
                intent,
                serve_url,
                page_url,
                title,
                f"r{round_i}-lote{bi}/{len(batches)}(n={len(batch)})",
            )
            total_ms += ms
            winners.append(w)
        seen: set[str] = set()
        pool = []
        for w in winners:
            if w.key not in seen:
                seen.add(w.key)
                pool.append(w)
        if shuffle_pool:
            random.shuffle(pool)
        round_i += 1

    return pool[0], total_ms, last_conf


def confirm_match(chosen: Candidate, intent: str, serve_url: str) -> tuple[float, float]:
    """noul: does this candidate satisfy the intent?"""
    state = f"User intent: {intent}\nCandidate:\n{chosen.summary}"
    questions = {
        "matches": {
            "type": "noul",
            "instructions": (
                "Does this candidate correctly match the user intent? "
                "Yes only if text/href/label clearly matches what they asked for. "
                "No if it is a different control (e.g. Ajuda/Help when they asked Cadastrar)."
            ),
        }
    }
    result, ms = laya_request(serve_url, state, questions)
    return float(result["answers"]["matches"]["noul"]), ms


def by_key(cands: list[Candidate], key: str) -> Candidate:
    for c in cands:
        if c.key == key:
            return c
    raise KeyError(key)


def _emit_json(payload: dict, json_stdout, *, exit_code: int | None = None) -> int:
    print(emit_json_line(payload), file=json_stdout)
    if exit_code is not None:
        return exit_code
    return 0 if payload.get("ok") else 1


def _run_impl(options: FindOptions) -> int:
    _reconfigure_stdout()
    json_stdout = sys.stdout
    if options.json_stdout:
        sys.stdout = sys.stderr
    if not options.url or not options.intent or not options.mode:
        print("URL, modo e intent são obrigatórios.", file=sys.stderr)
        if options.json_stdout:
            return _emit_json(
                build_result(
                    ok=False,
                    url=options.url or "",
                    final_url=options.url or "",
                    intent=options.intent or "",
                    kind=options.kind or "",
                    policy=options.policy,
                ),
                json_stdout,
                exit_code=2,
            )
        return 2
    batch_size = max(2, options.batch_size)

    try:
        health = check_serve(options.serve)
    except urllib.error.URLError as exc:
        print(f"laya-serve offline em {options.serve}: {exc}", file=sys.stderr)
        if options.json_stdout:
            return _emit_json(
                build_result(
                    ok=False,
                    url=options.url,
                    final_url=options.url,
                    intent=options.intent,
                    kind=options.kind or "",
                    policy=options.policy,
                ),
                json_stdout,
            )
        return 1

    print(f"laya-serve ok · loaded={health.get('loaded')}")
    print(f"url={options.url}")
    print(f"mode={options.mode} · intent={options.intent!r}")

    # --- Phase 0: classify intent → kind ---
    choice_conf: float | None = None
    if options.kind:
        kind = options.kind
        print(f"kind={kind} (override --kind)")
    else:
        kind, ms_kind = classify_intent(options.intent, options.mode, options.serve)
        print(f"fase 0 · kind={kind} ({ms_kind:.0f} ms)")

    confirm_noul: float | None = None
    selector_cache = CacheStore.load(options.cache_path) if options.use_cache else None
    selector_cache_key = cache_key(options.url, options.intent)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not options.headed)
        page = browser.new_page()
        page.set_default_timeout(options.timeout_ms)

        cands: list[Candidate] = []
        detach_net = None
        to_net_cands = None
        need_net = kind == "network" or options.mode in ("network", "both")

        if need_net:
            _seen, detach_net, to_net_cands = capture_network(
                page, options.listen_seconds, attach_only=True
            )

        page.goto(options.url, wait_until="domcontentloaded")
        settle_page(
            page,
            options.settle_ms,
            kind if kind != "network" else "input",
            reveal=options.reveal,
        )

        if selector_cache is not None and cache_lookup_allowed(options.mode, kind):
            had_cached_record = selector_cache.get(selector_cache_key) is not None
            cached = resolve_cache_hit(selector_cache, selector_cache_key, page)
            if cached is not None:
                cached_record, cached_matches = cached
                cached_selector = str(cached_record.get("selector") or "")
                cached_kind = str(cached_record.get("kind") or kind)
                cached_href = str(cached_record.get("href_hint") or "")
                print(f"cache hit · selector={cached_selector} matches={cached_matches}")
                final_url = page.url
                browser.close()
                if options.json_stdout:
                    return _emit_json(
                        build_result(
                            ok=True,
                            url=options.url,
                            final_url=final_url,
                            intent=options.intent,
                            kind=cached_kind,
                            selector=cached_selector,
                            selector_ok=True,
                            matches=cached_matches,
                            href=cached_href,
                            policy=options.policy,
                            cached=True,
                        ),
                        json_stdout,
                    )
                return 0
            if had_cached_record:
                print("cache inválido · removendo e redescobrindo")

        if need_net:
            print(f"ouvindo network por {options.listen_seconds:.1f}s …")
            if options.headed:
                print("(headed: interaja na página para gerar requests)")
            page.wait_for_timeout(int(options.listen_seconds * 1000))
            if detach_net:
                detach_net()
            if to_net_cands:
                net = to_net_cands()
                if kind == "network" or options.mode == "both":
                    cands.extend(net)

        if kind != "network" and options.mode in ("dom", "both"):
            kinds = collection_kinds(kind)
            print(f"coletando DOM kinds={sorted(kinds)}")
            cands.extend(extract_dom(page, kinds))
        elif options.mode == "dom" and kind == "network":
            # classify said network but mode is dom — collect inputs as fallback
            cands.extend(extract_dom(page, {"input"}))

        if not cands:
            print(
                f"Nenhum candidato kind={kind}. "
                "Tente --headed, --settle-ms 3000, ou URL de login direta.",
                file=sys.stderr,
            )
            browser.close()
            if options.json_stdout:
                return _emit_json(
                    build_result(
                        ok=False,
                        url=options.url,
                        final_url=page.url,
                        intent=options.intent,
                        kind=kind,
                        policy=options.policy,
                    ),
                    json_stdout,
                )
            return 1

        print("-" * 72)
        before = len(cands)
        cands = dedupe_by_destination(cands)
        after_dest = len(cands)
        cands = apply_policy(cands, options.intent, options.policy)
        print(
            f"Candidatos kind={kind}: {before} → dest={after_dest} → "
            f"policy={options.policy}: {len(cands)}"
        )
        for c in cands[:30]:
            print(f"  {c.summary}")
        if len(cands) > 30:
            print(f"  … +{len(cands) - 30} omitidos na listagem")
        print("-" * 72)

        # --- Phases: tournament or single shot ---
        if options.no_tournament:
            pool = list(cands)
            if options.policy == "none":
                random.shuffle(pool)
            pool = pool[:batch_size]
            chosen, total_ms, choice_conf = choose_one(
                pool, options.intent, options.serve, page.url, page.title(), f"single(n={len(pool)})"
            )
        else:
            chosen, total_ms, choice_conf = tournament(
                cands,
                options.intent,
                options.serve,
                page.url,
                page.title(),
                batch_size,
                shuffle_pool=options.policy == "none",
            )

        if not options.no_confirm:
            confirm_noul, ms_c = confirm_match(chosen, options.intent, options.serve)
            print(f"confirmação noul={confirm_noul:.2f} ({ms_c:.0f} ms) — P(atende o intent)")

        # Single fallback pass: low-confidence winners are retried only among
        # candidates whose visible text or href overlaps meaningful intent tokens.
        low_confirm = confirm_noul is not None and confirm_noul < 0.5
        low_choice = choice_conf is not None and choice_conf < 0.25
        if low_confirm or low_choice:
            retry_pool = candidates_overlapping_intent(cands, options.intent)
            if retry_pool:
                print(
                    "fallback de baixa confiança: repetindo uma vez com "
                    f"{len(retry_pool)} candidato(s) com overlap text/href"
                )
                chosen, retry_ms, choice_conf = tournament(
                    retry_pool,
                    options.intent,
                    options.serve,
                    page.url,
                    page.title(),
                    batch_size,
                    shuffle_pool=options.policy == "none",
                )
                total_ms += retry_ms
                if not options.no_confirm:
                    confirm_noul, ms_c = confirm_match(
                        chosen, options.intent, options.serve
                    )
                    print(
                        f"confirmação fallback noul={confirm_noul:.2f} "
                        f"({ms_c:.0f} ms)"
                    )
            else:
                print(
                    "fallback de baixa confiança indisponível: "
                    "nenhum candidato com overlap text/href",
                    file=sys.stderr,
                )

        print("-" * 72)
        print(f"vencedor ({total_ms:.0f} ms em choices)")
        if chosen.source == "dom":
            chosen = repair_selector(page, chosen)
        print(f"  {chosen.summary}")
        sel_ok = False
        match_n = 0
        if chosen.selector:
            sel_ok, match_n = verify_selector(page, chosen.selector)
            print(f"  selector: {chosen.selector}")
            print(f"  selector_ok={sel_ok} matches={match_n} (querySelector/Playwright)")
        if chosen.request:
            print(f"  request: {chosen.request.get('method')} {chosen.request.get('url')}")

        if confirm_noul is not None and confirm_noul < 0.5:
            print("aviso: confiança baixa; candidato pode não ser o certo.", file=sys.stderr)

        if selector_cache is not None and save_cache_candidate(
            selector_cache, selector_cache_key, chosen, sel_ok, match_n
        ):
            print(f"cache salvo · selector={chosen.selector}")
        elif selector_cache is not None and chosen.selector and is_volatile_selector(chosen.selector):
            print("cache não salvo · seletor volátil", file=sys.stderr)

        final_url = page.url
        browser.close()

    if options.json_stdout:
        href = chosen.href or summary_field(chosen.summary, "href")
        text = summary_field(chosen.summary, "text")
        return _emit_json(
            build_result(
                ok=True,
                url=options.url,
                final_url=final_url,
                intent=options.intent,
                kind=kind,
                selector=chosen.selector,
                selector_ok=sel_ok,
                matches=match_n,
                href=href,
                text=text,
                confidence=choice_conf,
                confirm_noul=confirm_noul,
                policy=options.policy,
                cached=False,
            ),
            json_stdout,
        )
    return 0


def run(options: FindOptions) -> int:
    """Run discovery while preserving the JSON contract on unexpected failures."""
    json_stdout = sys.stdout
    try:
        return _run_impl(options)
    except Exception as exc:
        if not options.json_stdout:
            print(f"Falha inesperada: {exc}", file=sys.stderr)
            return 1
        print(f"Falha inesperada: {exc}", file=sys.stderr)
        return _emit_json(
            build_result(
                ok=False,
                url=options.url or "",
                final_url=options.url or "",
                intent=options.intent or "",
                kind=options.kind or "",
                text=str(exc),
                policy=options.policy,
            ),
            json_stdout,
            exit_code=1,
        )
    finally:
        sys.stdout = json_stdout

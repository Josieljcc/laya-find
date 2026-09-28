from laya_find.find import (
    collection_kinds,
    extract_dom,
    heuristic_kind,
)


SAMPLE_HTML = """
<html><body>
<div data-sortable-type="secao" data-parent-id="0">
  <div data-id="1" wire:key="secao-1">
    <div>
      <div class="flex cursor-pointer items-center" x-on:click="abrir()">
        <span>Aulas</span>
        <button type="button" aria-expanded="false" aria-label="Expandir">v</button>
      </div>
    </div>
  </div>
  <div data-id="2" wire:key="secao-2">
    <div>
      <div class="flex cursor-pointer items-center" x-on:click="abrir()">
        <span>Ebook</span>
        <button type="button" aria-expanded="true" aria-label="Recolher">v</button>
      </div>
    </div>
  </div>
</div>
<div data-sortable-type="aula">
  <div data-id="10" data-linha-abrir class="linha-lista cursor-pointer">Aula 1</div>
  <div data-id="11" data-linha-abrir class="linha-lista cursor-pointer">Aula 2</div>
</div>
<button type="button" id="real-btn">Salvar</button>
<a href="/x">Link</a>
</body></html>
"""


def test_heuristic_maps_collapse_to_clickable():
    assert heuristic_kind("cabeçalho collapse do módulo", "dom") == "clickable"
    assert heuristic_kind("div clicável expandir", "dom") == "clickable"
    assert heuristic_kind("botão entrar", "dom") == "button"


def test_collection_kinds_clickable_only():
    assert collection_kinds("clickable") == {"clickable"}


def test_extract_dom_clickable_finds_headers_not_native_controls(page_factory=None):
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(SAMPLE_HTML)
        cands = extract_dom(page, {"clickable"})
        browser.close()

    assert cands, "expected clickable candidates"
    kinds = {c.kind for c in cands}
    assert kinds == {"clickable"}
    texts = " ".join(c.summary for c in cands)
    assert "Aulas" in texts or "Ebook" in texts or "cursor-pointer" in texts
    # Should not classify the native button/link as clickable host
    assert "kind=clickable" in cands[0].summary
    selectors = [c.selector for c in cands if c.selector]
    assert selectors
    # Prefer a list-friendly selector when possible
    multi = [
        s
        for s in selectors
        if "cursor-pointer" in s or "data-linha-abrir" in s or "data-sortable-type" in s
    ]
    assert multi, f"expected list-oriented selector, got {selectors}"

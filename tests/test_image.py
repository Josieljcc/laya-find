from laya_find.find import collection_kinds, extract_dom, heuristic_kind


SAMPLE_HTML = """
<html><body>
<div data-sortable-type="secao">
  <div data-id="1">
    <button type="button" aria-label="Alterar imagem">
      <img src="/thumbs/a.png" alt="Aulas" width="88" height="88">
    </button>
  </div>
  <div data-id="2">
    <button type="button" aria-label="Alterar imagem">
      <img src="/thumbs/b.png" alt="Ebook" width="88" height="88">
    </button>
  </div>
</div>
<img src="data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7" width="1" height="1" alt="">
<button type="button">Salvar</button>
</body></html>
"""


def test_heuristic_maps_imagem_to_image():
    assert heuristic_kind("imagem do módulo", "dom") == "image"
    assert heuristic_kind("thumbnail da aula", "dom") == "image"
    assert heuristic_kind("botão entrar", "dom") == "button"


def test_collection_kinds_image_only():
    assert collection_kinds("image") == {"image"}


def test_extract_dom_image_finds_imgs():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(SAMPLE_HTML)
        cands = extract_dom(page, {"image"})
        browser.close()

    assert len(cands) >= 2
    assert all(c.kind == "image" for c in cands)
    joined = " ".join(c.summary for c in cands)
    assert "Aulas" in joined or "alt=Aulas" in joined
    selectors = [c.selector for c in cands if c.selector]
    assert any(
        "img" in s and ("alt" in s or "data-sortable-type" in s or s == "img" or "button img" in s)
        for s in selectors
    ), selectors

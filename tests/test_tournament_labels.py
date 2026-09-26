def test_short_label_includes_text_and_stable_href_hint():
    from examples.laya_find_lib.decide import short_label

    label = short_label(
        text="Cadastrar agora",
        href="https://dashboard.kiwify.com/signup?lang=pt&country=br",
        kind="link",
    )
    assert "Cadastrar agora" in label
    assert "signup" in label.lower()
    assert "lang=pt" not in label

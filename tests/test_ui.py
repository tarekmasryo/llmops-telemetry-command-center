from src import ui


def test_esc_escapes_html_characters() -> None:
    assert ui.esc('<script>alert("x")</script>') == "&lt;script&gt;alert(&quot;x&quot;)&lt;/script&gt;"


def test_badge_escapes_text_and_uses_known_class() -> None:
    html = ui.badge("<b>critical</b>", kind="critical")
    assert "<b>" not in html
    assert "&lt;b&gt;critical&lt;/b&gt;" in html
    assert "badge-red" in html


def test_clean_html_dedents_and_strips() -> None:
    fragment = """
        <div>
          content
        </div>
    """
    assert ui.clean_html(fragment).startswith("<div>")
    assert ui.clean_html(fragment).endswith("</div>")


def test_key_value_grid_uses_columns_and_escapes_values(monkeypatch) -> None:
    rendered: list[str] = []
    monkeypatch.setattr(ui, "render_html", rendered.append)

    ui.key_value_grid([("Name", "<unsafe>")], columns=3)

    assert rendered
    assert "repeat(3, minmax(0, 1fr))" in rendered[0]
    assert "&lt;unsafe&gt;" in rendered[0]
    assert "<unsafe>" not in rendered[0]

from slot_watch.checker import normalize_text, visible_text


def test_normalize_text_is_case_and_whitespace_insensitive() -> None:
    assert normalize_text("  No\n SLOTS\u00a0Available ") == "no slots available"


def test_visible_text_ignores_script_and_style_content() -> None:
    document = """
    <html>
      <style>.empty { content: "No slots"; }</style>
      <script>const message = "No slots";</script>
      <body><p>Booking calendar</p></body>
    </html>
    """
    assert visible_text(document) == "booking calendar"


def test_visible_text_decodes_entities() -> None:
    assert visible_text("<p>No&nbsp;appointments &amp; no queue</p>") == (
        "no appointments & no queue"
    )

from slot_watch.checker import PageChecker


def make_checker() -> PageChecker:
    return PageChecker(
        url="https://example.com",
        empty_text="Наразі всі місця зайняті.",
        required_text="Електронна черга за адресою Варна",
        timeout_seconds=5,
        user_agent="test",
    )


def test_classifies_empty_page() -> None:
    result = make_checker().classify(
        "<h1>Електронна черга за адресою Варна</h1>"
        "<p>Наразі всі місця зайняті.</p>"
    )
    assert result.available is False


def test_classifies_page_without_empty_marker_as_available() -> None:
    result = make_checker().classify(
        "<h1>Електронна черга за адресою Варна</h1><button>10:30</button>"
    )
    assert result.available is True


def test_rejects_unexpected_page_instead_of_false_alert() -> None:
    try:
        make_checker().classify("<h1>Temporarily unavailable</h1>")
    except ValueError as error:
        assert "expected booking-page heading" in str(error)
    else:
        raise AssertionError("unexpected page was classified as available")

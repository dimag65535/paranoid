import pytest

from slot_watch.config import _user_ids


def test_user_ids_parses_comma_separated_values(monkeypatch) -> None:
    monkeypatch.setenv("TEST_USER_IDS", "123, 456,123")
    assert _user_ids("TEST_USER_IDS") == frozenset({123, 456})


@pytest.mark.parametrize("value", ["", "123,nope", "0", "-10"])
def test_user_ids_rejects_invalid_values(monkeypatch, value: str) -> None:
    monkeypatch.setenv("TEST_USER_IDS", value)
    with pytest.raises(ValueError):
        _user_ids("TEST_USER_IDS")

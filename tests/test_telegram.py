import pytest

from slot_watch import telegram
from slot_watch.telegram import Telegram, TelegramNetworkError


def test_call_wraps_timeout_as_retryable_network_error(monkeypatch) -> None:
    def timeout(*args, **kwargs):
        raise TimeoutError("read timed out")

    monkeypatch.setattr(telegram, "urlopen", timeout)

    with pytest.raises(TelegramNetworkError, match="read timed out"):
        Telegram("token").call("getMe")


def test_get_updates_uses_timeout_with_network_margin(monkeypatch) -> None:
    recorded: dict = {}
    client = Telegram("token")

    def call(method, **parameters):
        recorded.update(method=method, **parameters)
        return []

    monkeypatch.setattr(client, "call", call)

    assert client.get_updates(offset=42) == []
    assert recorded["method"] == "getUpdates"
    assert recorded["timeout"] == 30
    assert recorded["request_timeout_seconds"] == 60
    assert recorded["offset"] == 42

from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class TelegramNetworkError(ConnectionError):
    """A retryable failure while reaching the Telegram Bot API."""


class Telegram:
    def __init__(self, token: str, timeout_seconds: int = 40) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.timeout_seconds = timeout_seconds

    def call(
        self,
        method: str,
        *,
        request_timeout_seconds: int | None = None,
        **parameters: Any,
    ) -> Any:
        body = urlencode(parameters).encode()
        request = Request(f"{self.base_url}/{method}", data=body)
        try:
            with urlopen(
                request,
                timeout=request_timeout_seconds or self.timeout_seconds,
            ) as response:
                payload = json.load(response)
        except HTTPError:
            raise
        except (TimeoutError, URLError, OSError) as error:
            raise TelegramNetworkError(str(error)) from error
        if not payload.get("ok"):
            raise RuntimeError(payload.get("description", "Telegram API error"))
        return payload["result"]

    def send_message(self, chat_id: int, text: str) -> None:
        self.call(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            disable_web_page_preview="true",
        )

    def get_updates(self, offset: int | None) -> list[dict[str, Any]]:
        poll_timeout_seconds = 30
        parameters: dict[str, Any] = {
            "timeout": poll_timeout_seconds,
            "allowed_updates": json.dumps(["message"]),
        }
        if offset is not None:
            parameters["offset"] = offset
        return self.call(
            "getUpdates",
            request_timeout_seconds=poll_timeout_seconds + 30,
            **parameters,
        )

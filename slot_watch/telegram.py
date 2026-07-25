from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class Telegram:
    def __init__(self, token: str, timeout_seconds: int = 40) -> None:
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.timeout_seconds = timeout_seconds

    def call(self, method: str, **parameters: Any) -> Any:
        body = urlencode(parameters).encode()
        request = Request(f"{self.base_url}/{method}", data=body)
        with urlopen(request, timeout=self.timeout_seconds) as response:
            payload = json.load(response)
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
        parameters: dict[str, Any] = {
            "timeout": 30,
            "allowed_updates": json.dumps(["message"]),
        }
        if offset is not None:
            parameters["offset"] = offset
        return self.call("getUpdates", **parameters)

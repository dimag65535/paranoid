from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


# Replace this with your numeric Telegram user ID. Add more IDs if needed.
AUTHORIZED_USER_IDS = frozenset({0})
DEFAULT_WATCH_URL = "https://varna.pasport.org.ua/solutions/e-queue"
DEFAULT_EMPTY_TEXT = "Наразі всі місця зайняті."
DEFAULT_REQUIRED_TEXT = "Електронна черга за адресою Варна"


@dataclass(frozen=True)
class Config:
    bot_token: str
    watch_url: str
    empty_text: str
    required_text: str
    interval_seconds: int
    jitter_seconds: int
    request_timeout_seconds: int
    user_agent: str
    page_cookie: str
    state_file: Path

    @classmethod
    def from_env(cls) -> "Config":
        config = cls(
            bot_token=_required_env("TELEGRAM_BOT_TOKEN"),
            watch_url=os.getenv("WATCH_URL", DEFAULT_WATCH_URL).strip(),
            empty_text=os.getenv("EMPTY_TEXT", DEFAULT_EMPTY_TEXT).strip(),
            required_text=os.getenv(
                "REQUIRED_TEXT", DEFAULT_REQUIRED_TEXT
            ).strip(),
            interval_seconds=_positive_int("CHECK_INTERVAL_SECONDS", 300),
            jitter_seconds=_nonnegative_int("CHECK_JITTER_SECONDS", 180),
            request_timeout_seconds=_positive_int("REQUEST_TIMEOUT_SECONDS", 30),
            user_agent=os.getenv(
                "USER_AGENT",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "Chrome/126 Safari/537.36",
            ),
            state_file=Path(os.getenv("STATE_FILE", "state.json")),
            page_cookie=os.getenv("PAGE_COOKIE", "").strip(),
        )
        if not AUTHORIZED_USER_IDS or AUTHORIZED_USER_IDS == {0}:
            raise ValueError(
                "Set AUTHORIZED_USER_IDS in slot_watch/config.py to your Telegram user ID"
            )
        return config


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _positive_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero")
    return value


def _nonnegative_int(name: str, default: int) -> int:
    value = int(os.getenv(name, str(default)))
    if value < 0:
        raise ValueError(f"{name} must be zero or greater")
    return value

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_WATCH_URL = "https://varna.pasport.org.ua/solutions/e-queue"
DEFAULT_EMPTY_TEXT = "Наразі всі місця зайняті."
DEFAULT_REQUIRED_TEXT = "Електронна черга за адресою Варна"


@dataclass(frozen=True)
class Config:
    bot_token: str
    allowed_user_ids: frozenset[int]
    watch_url: str
    empty_text: str
    required_text: str
    interval_seconds: int
    jitter_seconds: int
    page_load_timeout_seconds: int
    challenge_timeout_seconds: int
    firefox_binary: str
    geckodriver_path: str
    browser_profile_dir: Path
    state_file: Path

    @classmethod
    def from_env(cls) -> "Config":
        config = cls(
            bot_token=_required_env("TELEGRAM_BOT_TOKEN"),
            allowed_user_ids=_user_ids("TELEGRAM_ALLOWED_USER_IDS"),
            watch_url=os.getenv("WATCH_URL", DEFAULT_WATCH_URL).strip(),
            empty_text=os.getenv("EMPTY_TEXT", DEFAULT_EMPTY_TEXT).strip(),
            required_text=os.getenv(
                "REQUIRED_TEXT", DEFAULT_REQUIRED_TEXT
            ).strip(),
            interval_seconds=_positive_int("CHECK_INTERVAL_SECONDS", 300),
            jitter_seconds=_nonnegative_int("CHECK_JITTER_SECONDS", 180),
            page_load_timeout_seconds=_positive_int(
                "PAGE_LOAD_TIMEOUT_SECONDS", 30
            ),
            challenge_timeout_seconds=_positive_int(
                "CHALLENGE_TIMEOUT_SECONDS", 120
            ),
            firefox_binary=os.getenv(
                "FIREFOX_BINARY", "/snap/firefox/current/usr/lib/firefox/firefox"
            ).strip(),
            geckodriver_path=os.getenv(
                "GECKODRIVER_PATH", "/snap/bin/geckodriver"
            ).strip(),
            browser_profile_dir=Path(
                os.getenv("BROWSER_PROFILE_DIR", ".firefox-profile")
            ),
            state_file=Path(os.getenv("STATE_FILE", "state.json")),
        )
        return config


def _required_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise ValueError(f"{name} is required")
    return value


def _user_ids(name: str) -> frozenset[int]:
    raw_ids = _required_env(name)
    try:
        user_ids = frozenset(int(value.strip()) for value in raw_ids.split(","))
    except ValueError as error:
        raise ValueError(f"{name} must contain comma-separated numeric IDs") from error
    if any(user_id <= 0 for user_id in user_ids):
        raise ValueError(f"{name} must contain positive numeric IDs")
    return user_ids


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

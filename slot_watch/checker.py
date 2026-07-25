from __future__ import annotations

import html
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from urllib.request import Request, urlopen


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self.parts.append(data)


def normalize_text(value: str) -> str:
    return " ".join(html.unescape(value).split()).casefold()


def visible_text(document: str) -> str:
    parser = _VisibleTextParser()
    parser.feed(document)
    return normalize_text(" ".join(parser.parts))


@dataclass(frozen=True)
class CheckResult:
    available: bool
    checked_at: str
    page_text_length: int


class PageChecker:
    def __init__(
        self,
        url: str,
        empty_text: str,
        required_text: str,
        timeout_seconds: int,
        user_agent: str,
        cookie: str = "",
    ) -> None:
        self.url = url
        self.empty_text = normalize_text(empty_text)
        self.required_text = normalize_text(required_text)
        self.timeout_seconds = timeout_seconds
        self.user_agent = user_agent
        self.cookie = cookie

    def check(self) -> CheckResult:
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "uk-UA,uk;q=0.9,en;q=0.8",
            "Cache-Control": "no-cache",
        }
        if self.cookie:
            headers["Cookie"] = self.cookie
        request = Request(self.url, headers=headers)
        with urlopen(request, timeout=self.timeout_seconds) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            document = response.read().decode(charset, errors="replace")

        return self.classify(document)

    def classify(self, document: str) -> CheckResult:
        text = visible_text(document)
        if self.required_text not in text:
            raise ValueError("Response does not contain the expected booking-page heading")
        return CheckResult(
            available=self.empty_text not in text,
            checked_at=datetime.now(UTC).isoformat(),
            page_text_length=len(text),
        )

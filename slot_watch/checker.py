from __future__ import annotations

import html
import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from html.parser import HTMLParser
from pathlib import Path


LOG = logging.getLogger("slot_watch.checker")


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
        page_load_timeout_seconds: int,
        challenge_timeout_seconds: int,
        profile_dir: Path,
        firefox_binary: str,
        geckodriver_path: str,
    ) -> None:
        self.url = url
        self.empty_text = normalize_text(empty_text)
        self.required_text = normalize_text(required_text)
        self.page_load_timeout_seconds = page_load_timeout_seconds
        self.challenge_timeout_seconds = challenge_timeout_seconds
        self.profile_dir = profile_dir
        self.firefox_binary = firefox_binary
        self.geckodriver_path = geckodriver_path
        self._driver = None

    def check(self) -> CheckResult:
        from selenium.common.exceptions import (
            InvalidSessionIdException,
            NoSuchWindowException,
        )

        for attempt in range(2):
            try:
                driver = self._driver or self._start_browser()
                return self._check_with_browser(driver)
            except (InvalidSessionIdException, NoSuchWindowException):
                self.close()
                if attempt:
                    raise
                LOG.warning("Firefox was closed; starting a new browser session")
        raise RuntimeError("Firefox session could not be started")

    def _start_browser(self):
        from selenium import webdriver
        from selenium.webdriver.firefox.options import Options
        from selenium.webdriver.firefox.service import Service

        self.profile_dir.mkdir(parents=True, exist_ok=True)
        options = Options()
        if self.firefox_binary:
            options.binary_location = self.firefox_binary
        options.add_argument("-profile")
        options.add_argument(str(self.profile_dir.resolve()))
        service = Service(executable_path=self.geckodriver_path or None)
        self._driver = webdriver.Firefox(options=options, service=service)
        self._driver.set_page_load_timeout(self.page_load_timeout_seconds)
        LOG.info("Started visible Firefox with profile %s", self.profile_dir)
        return self._driver

    def _check_with_browser(self, driver) -> CheckResult:
        from selenium.common.exceptions import TimeoutException

        try:
            driver.get(self.url)
        except TimeoutException:
            LOG.warning("Page load timed out; checking the current browser content")

        deadline = time.monotonic() + self.challenge_timeout_seconds
        waiting_logged = False
        while True:
            document = driver.page_source
            text = visible_text(document)
            if self.required_text in text:
                return self._result_from_text(text)
            if time.monotonic() >= deadline:
                title = driver.title
                raise ValueError(
                    "Expected booking page did not appear within "
                    f"{self.challenge_timeout_seconds}s; browser title: {title!r}"
                )
            if not waiting_logged:
                LOG.warning(
                    "Waiting up to %s seconds for the booking page; "
                    "complete any challenge in Firefox",
                    self.challenge_timeout_seconds,
                )
                waiting_logged = True
            time.sleep(1)

    def classify(self, document: str) -> CheckResult:
        text = visible_text(document)
        if self.required_text not in text:
            raise ValueError("Response does not contain the expected booking-page heading")
        return self._result_from_text(text)

    def _result_from_text(self, text: str) -> CheckResult:
        return CheckResult(
            available=self.empty_text not in text,
            checked_at=datetime.now(UTC).isoformat(),
            page_text_length=len(text),
        )

    def close(self) -> None:
        if self._driver is None:
            return
        try:
            self._driver.quit()
        except Exception:
            LOG.warning("Could not close Firefox cleanly", exc_info=True)
        finally:
            self._driver = None

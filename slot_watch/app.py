from __future__ import annotations

import logging
import random
import signal
import threading
from datetime import datetime

from slot_watch.checker import PageChecker
from slot_watch.config import Config
from slot_watch.state import WatchState, load_state, save_state
from slot_watch.telegram import Telegram

LOG = logging.getLogger("slot_watch")


class Application:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.telegram = Telegram(config.bot_token)
        self.checker = PageChecker(
            config.watch_url,
            config.empty_text,
            config.required_text,
            config.page_load_timeout_seconds,
            config.challenge_timeout_seconds,
            config.browser_profile_dir,
            config.firefox_binary,
            config.geckodriver_path,
        )
        self.state = load_state(config.state_file)
        self.stop_event = threading.Event()
        self.check_lock = threading.Lock()

    def run(self) -> None:
        signal.signal(signal.SIGTERM, lambda *_: self.stop_event.set())
        signal.signal(signal.SIGINT, lambda *_: self.stop_event.set())
        listener = threading.Thread(
            target=self._listen_for_commands, name="telegram-listener", daemon=True
        )
        listener.start()
        LOG.info("Watching %s", self.config.watch_url)

        try:
            while not self.stop_event.is_set():
                self.check_once()
                delay = self.config.interval_seconds + random.uniform(
                    0, self.config.jitter_seconds
                )
                LOG.info("Next check in %.0f seconds", delay)
                self.stop_event.wait(delay)
        finally:
            self.checker.close()

    def check_once(self) -> None:
        if not self.check_lock.acquire(blocking=False):
            return
        try:
            previous = self.state.available
            result = self.checker.check()
            next_state = WatchState(
                available=result.available,
                checked_at=result.checked_at,
                last_error=None,
            )

            if result.available and previous is not True:
                self._broadcast(
                    "SLOT MAY BE AVAILABLE\n\n"
                    f"The empty-state text disappeared:\n{self.config.watch_url}"
                )
            elif previous is True and not result.available:
                self._broadcast(
                    "Slots are unavailable again.\n\n"
                    f"The empty-state text is back:\n{self.config.watch_url}"
                )

            self.state = next_state
            save_state(self.config.state_file, self.state)
            LOG.info(
                "Check complete: available=%s, text_length=%d",
                result.available,
                result.page_text_length,
            )
        except Exception as error:
            LOG.exception("Check or notification failed")
            self.state.last_error = f"{type(error).__name__}: {error}"
            save_state(self.config.state_file, self.state)
        finally:
            self.check_lock.release()

    def _broadcast(self, text: str) -> None:
        for user_id in self.config.allowed_user_ids:
            self.telegram.send_message(user_id, text)

    def _listen_for_commands(self) -> None:
        offset: int | None = None
        while not self.stop_event.is_set():
            try:
                updates = self.telegram.get_updates(offset)
                for update in updates:
                    offset = update["update_id"] + 1
                    self._handle_update(update)
            except Exception:
                LOG.exception("Telegram polling failed")
                self.stop_event.wait(5)

    def _handle_update(self, update: dict) -> None:
        message = update.get("message", {})
        sender_id = message.get("from", {}).get("id")
        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "").split("@", 1)[0].split(maxsplit=1)[0]
        if (
            sender_id not in self.config.allowed_user_ids
            or not isinstance(chat_id, int)
        ):
            LOG.warning("Ignored unauthorized Telegram user %s", sender_id)
            return

        if text in {"/start", "/status"}:
            self.telegram.send_message(chat_id, self._status_text())
        elif text == "/check":
            self.telegram.send_message(chat_id, "Checking now.")
            threading.Thread(target=self.check_once, daemon=True).start()
        else:
            self.telegram.send_message(chat_id, "Commands: /status, /check")

    def _status_text(self) -> str:
        labels = {None: "not checked yet", False: "empty / no slots", True: "possible slot"}
        checked = self.state.checked_at or "never"
        try:
            checked = datetime.fromisoformat(checked).astimezone().strftime(
                "%Y-%m-%d %H:%M:%S %Z"
            )
        except ValueError:
            pass
        text = f"Status: {labels[self.state.available]}\nLast check: {checked}"
        if self.state.last_error:
            text += f"\nLast error: {self.state.last_error}"
        return text


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(threadName)s %(message)s",
    )
    try:
        config = Config.from_env()
    except (ValueError, TypeError) as error:
        raise SystemExit(f"Configuration error: {error}") from error
    Application(config).run()


if __name__ == "__main__":
    main()

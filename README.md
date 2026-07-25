# Slot Watch Telegram Bot

The bot checks a booking page every 5-8 minutes by default. It treats the page
as empty while `EMPTY_TEXT` is visible and sends one Telegram notification each
time that state changes. State is stored in `state.json`, so restarts do not
produce duplicate alerts.

## Configure

1. Create a bot with Telegram's `@BotFather` and get its token.
2. Get your numeric Telegram user ID (for example, from Telegram's
   `@userinfobot`).
3. Copy `.env.example` to `.env`.
4. Set `TELEGRAM_BOT_TOKEN` and your numeric ID in
   `TELEGRAM_ALLOWED_USER_IDS`. Multiple IDs are comma-separated.

The Varna booking URL and `Наразі всі місця зайняті.` marker are already the
defaults. `WATCH_URL` and `EMPTY_TEXT` can still override them later.

Install the project into your virtual environment, load `.env`, and run:

```bash
source .venv/bin/activate
pip install -e .
set -a
. ./.env
set +a
python3 -m slot_watch.app
```

Available commands are `/status` and `/check`. Messages from IDs outside the
configured allowlist are ignored.

## Keep it running

`slot-watch.service.example` is a systemd unit template. Adjust its paths, copy
it to `/etc/systemd/system/slot-watch.service`, then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now slot-watch
```

## Firefox session

The bot opens a visible Firefox window and keeps it running with a dedicated
profile in `.firefox-profile`. On the first launch, complete any Cloudflare prompt
in that window. The bot waits up to `CHALLENGE_TIMEOUT_SECONDS` for the booking
page and reuses the resulting browser session and cookies for later checks. Do not
close the window while the bot is running.

A visible browser requires a graphical desktop session. The example systemd unit
needs access to that session's `DISPLAY` and X authorization; foreground execution
is the simplest initial setup.

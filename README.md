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

Load `.env` and run:

```bash
set -a
. ./.env
set +a
python3 -m slot_watch.app
```

Available commands are `/status` and `/check`. Messages from IDs outside the
hardcoded allowlist are ignored.

## Keep it running

`slot-watch.service.example` is a systemd unit template. Adjust its paths, copy
it to `/etc/systemd/system/slot-watch.service`, then enable it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now slot-watch
```

## Limitation

The site may return a Cloudflare challenge to server or datacenter IP addresses.
This is treated as a check error and cannot create a false slot alert. If the machine
running the bot is challenged, open the page in a browser on that same machine and
network, then set `PAGE_COOKIE` to its Cookie request header (including the
`cf_clearance` value) and set `USER_AGENT` to that browser's exact user-agent.

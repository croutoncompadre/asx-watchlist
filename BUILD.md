# ASX Watchlist Bot - Build & Deployment Guide

This document covers everything you need to **build, run, and update** your ASX Watchlist Discord bot on a NAS or Linux server using Docker.

---

## 📂 Folder Structure

Recommended directory: `/home/neil/dockerapps/asx-catalyst-bot/`

```
/home/neil/dockerapps/asx-catalyst-bot/
│── Dockerfile
│── compose.yaml
│── requirements.txt
│── config.yaml          # shared by both bots
│── .env
│── asx_watchlist_bot.py # watchlist bot (RSS feeds)
│── asx_discord_commands.py # discord commands bot
│── data/                # persistent SQLite DBs for both bots
```

---

## 🐳 Docker Setup

### .env

```env
WATCHLIST_WEBHOOK_URL=YOUR_WEBHOOK_URL_HERE
DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DISCORD_GUILD_ID=YOUR_GUILD_ID_HERE
```

> Keep secrets out of `config.yaml`; always use `.env` for the webhook and bot token.

---

## ⚙️ Configuration

### config.yaml

- `watchlist`: list of ASX codes to monitor
- `poll_interval_seconds`: frequency of checking for new announcements
- `log_level`: logging level (DEBUG, INFO, WARNING, ERROR)

### Example snippet

```yaml
log_level: DEBUG
poll_interval_seconds: 300
watchlist:
  - CSL
  - ANZ
  - WBC
  - BHP
```

---

## 🤖 Discord Commands

The Discord bot provides slash commands to manage your watchlist:

- **`/watching`** - View current watchlist
- **`/add <ticker>`** - Add a ticker to watchlist (e.g., `/add CSL`)
- **`/remove <ticker>`** - Remove a ticker from watchlist (e.g., `/remove ANZ`)
- **`/clear_tickers`** - Clear all tickers from watchlist

### Ticker Format
- Must be 2-5 alphanumeric characters
- Examples: `CSL`, `ANZ`, `BHP`, `WBC`
- Automatically converted to uppercase

---

## 🚀 Build & Run

```bash
cd /home/neil/dockerapps/asx-catalyst-bot

# Build Docker image
docker compose build --no-cache

# Start containers in detached mode
docker compose up -d

# View logs
docker compose logs -f
```

---

## 🔄 Updating the Bot

1. **Edit code/config** (`asx_watchlist_bot.py`, `asx_discord_commands.py`, `config.yaml`, `requirements.txt`) as needed
2. **Rebuild image**:
   ```bash
   docker compose build
   ```
3. **Restart containers**:
   ```bash
   docker compose up -d
   ```
4. Persistent data (SQLite DB in `./data`) remains intact

---

## ⚠️ Troubleshooting

- **No messages in Discord**:
  - Check webhook in `.env`
  - Check logs: `docker compose logs -f`
  - Set `log_level: DEBUG` in `config.yaml` for more detail
  - Verify watchlist stocks are in `config.yaml`

- **Bot not running**:
  - Ensure Docker is installed and running
  - Check container status:
    ```bash
    docker ps -a
    ```

- **Updating dependencies**:
  - Edit `requirements.txt` and rebuild container

- **Discord commands not working**:
  - Ensure `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID` are set in `.env`
  - Check bot has proper permissions in Discord server
  - Verify bot is in the correct guild/server

---

## 💡 Tips

- The watchlist bot monitors multiple RSS feeds for news about your watchlist stocks.
- Keep your watchlist focused to avoid noise from irrelevant announcements.
- The bot automatically de-duplicates announcements using SQLite (`./data/seen_watchlist.db`).
- Use Discord slash commands to manage your watchlist without editing config files.
- For effortless updates, you can link this directory to a Git repository and pull updates before rebuilding.

---

## 📌 References

- Docker Docs: https://docs.docker.com/
- Docker Compose Docs: https://docs.docker.com/compose/
- Discord Webhooks: https://discord.com/developers/docs/resources/webhook
- Discord Bot API: https://discord.com/developers/docs/intro

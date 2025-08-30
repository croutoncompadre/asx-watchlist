# ASX Watchlist Discord Bot

A Docker-based Discord bot that monitors RSS feeds for ASX stock announcements and provides Discord slash commands to manage your watchlist.

## 🚀 Features

- **RSS Feed Monitoring**: Automatically monitors multiple Australian financial news RSS feeds
- **Watchlist Management**: Discord slash commands to add/remove stocks from your watchlist
- **Smart Filtering**: Only posts announcements for stocks in your watchlist
- **Priority Detection**: Automatically categorizes announcements (earnings, dividends, M&A, etc.)
- **Deduplication**: Prevents duplicate announcements using SQLite database
- **Docker Ready**: Easy deployment with Docker Compose

## 📋 Prerequisites

- Docker and Docker Compose installed
- Discord Bot Token
- Discord Webhook URL
- Discord Guild (Server) ID

## 🛠️ Setup

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd asx-watchlist
```

### 2. Environment Configuration

Create a `.env` file in the project root:

```env
WATCHLIST_WEBHOOK_URL=YOUR_WEBHOOK_URL_HERE
DISCORD_BOT_TOKEN=YOUR_BOT_TOKEN_HERE
DISCORD_GUILD_ID=YOUR_GUILD_ID_HERE
```

### 3. Configure Watchlist

Edit `config.yaml` to set your initial watchlist and preferences:

```yaml
log_level: DEBUG  # Options: DEBUG, INFO, WARNING, ERROR
poll_interval_seconds: 300  # Check RSS feeds every 5 minutes
watchlist:
  - CSL
  - ANZ
  - WBC
  - BHP
```

### 4. Build and Run

```bash
# Build Docker images
docker compose build --no-cache

# Start the bots
docker compose up -d

# View logs
docker compose logs -f
```

## 🤖 Discord Commands

Once the bot is running, you can use these slash commands in your Discord server:

| Command | Description | Example |
|---------|-------------|---------|
| `/watching` | View current watchlist | `/watching` |
| `/add <ticker>` | Add ticker to watchlist | `/add CSL` |
| `/remove <ticker>` | Remove ticker from watchlist | `/remove ANZ` |
| `/clear_tickers` | Clear all tickers from watchlist | `/clear_tickers` |

### Ticker Format
- Must be 2-5 alphanumeric characters
- Examples: `CSL`, `ANZ`, `BHP`, `WBC`
- Automatically converted to uppercase

## 📊 RSS Feeds Monitored

The bot monitors these Australian financial news sources:

- Small Caps
- Fat Tail Daily
- BetaShares
- Kalkine Media
- Australian Stock Report
- Stockhead
- Rask Media
- Stock Radar
- Motley Fool Australia
- Market Matters
- Aus Investors

## 🔧 Configuration

### config.yaml Options

- `log_level`: Logging verbosity (DEBUG, INFO, WARNING, ERROR)
- `poll_interval_seconds`: How often to check RSS feeds
- `watchlist`: List of ASX stock codes to monitor

### Environment Variables

- `WATCHLIST_WEBHOOK_URL`: Discord webhook URL for announcements
- `DISCORD_BOT_TOKEN`: Discord bot token for slash commands
- `DISCORD_GUILD_ID`: Discord server ID where commands are registered

## 🐳 Docker Services

The project runs two Docker containers:

1. **watchlist-bot**: Monitors RSS feeds and posts announcements
2. **discord-bot**: Handles Discord slash commands

## 📁 Project Structure

```
asx-watchlist/
├── asx_watchlist_bot.py      # RSS monitoring bot
├── asx_discord_commands.py   # Discord commands bot
├── config.yaml              # Configuration file
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker image definition
├── compose.yaml            # Docker Compose configuration
├── BUILD.md               # Detailed build guide
├── data/                  # SQLite databases (auto-created)
└── .env                   # Environment variables (create this)
```

## 🔄 Updating

1. **Edit code/config** as needed
2. **Rebuild and restart**:
   ```bash
   docker compose build
   docker compose up -d
   ```

## 🐛 Troubleshooting

### No Messages in Discord
- Check webhook URL in `.env`
- Verify watchlist stocks in `config.yaml`
- Check logs: `docker compose logs -f`
- Set `log_level: DEBUG` for more detail

### Bot Commands Not Working
- Ensure `DISCORD_BOT_TOKEN` and `DISCORD_GUILD_ID` are set
- Check bot has proper permissions in Discord server
- Verify bot is in the correct guild/server

### Container Issues
- Check container status: `docker ps -a`
- View logs: `docker compose logs -f`
- Ensure Docker is running

## 📝 Logs

View logs for both services:

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f watchlist
docker compose logs -f discord
```

## 🔒 Security Notes

- Never commit `.env` file to version control
- Keep your Discord bot token and webhook URL secure
- The `data/` directory contains SQLite databases and is excluded from git

## 📄 License

[Add your license information here]

## 🤝 Contributing

[Add contribution guidelines here]

---

For detailed build and deployment instructions, see [BUILD.md](BUILD.md).

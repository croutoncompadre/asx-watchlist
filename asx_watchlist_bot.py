#!/usr/bin/env python3
import feedparser
import sqlite3
import requests
import os
import time
import yaml
import re
from datetime import datetime, timedelta
import logging

# --- Environment ---
WEBHOOK_URL = os.getenv("WATCHLIST_WEBHOOK_URL")
DB_PATH = "./data/seen_watchlist.db"
PRUNE_DAYS = 30
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/config.yaml")

# RSS feeds from the catalyst bot
FEEDS = [
    "https://smallcaps.com.au/feed/",
    "https://daily.fattail.com.au/feed/",
    "https://www.betashares.com.au/feed/",
    "https://kalkinemedia.com/au/feed",
    "https://www.australianstockreport.com.au/insights/rss.xml",
    "https://stockhead.com.au/feed/",
    "https://www.raskmedia.com.au/feed/",
    "https://stockradar.com.au/feed/",
    "https://www.fool.com.au/feed/",
    "https://marketmatters.com.au/feed/",
    "https://ausinvestors.com/feed/",
]

os.makedirs("./data", exist_ok=True)

# --- Load config.yaml ---
with open(CONFIG_PATH, "r") as f:
    cfg = yaml.safe_load(f)

POLL_INTERVAL = cfg.get("poll_interval_seconds", 300)
LOG_LEVEL = cfg.get("log_level", "INFO").upper()
logging.basicConfig(level=getattr(logging, LOG_LEVEL),
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Initialize DB ---
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS seen (
    id TEXT PRIMARY KEY,
    timestamp DATETIME
)
""")
cur.execute("""
CREATE TABLE IF NOT EXISTS watchlist_snapshot (
    ticker TEXT PRIMARY KEY
)
""")
conn.commit()

# --- Load watchlist ---
def load_watchlist():
    with open(CONFIG_PATH, "r") as f:
        cfg = yaml.safe_load(f)
    return [t.upper() for t in cfg.get("watchlist", [])]

WATCHLIST = load_watchlist()

# --- Ticker extraction ---
def extract_ticker(title):
    """Extract ticker from title using multiple methods"""
    title_upper = title.upper()
    
    # Method 1: Check if ticker is after colon
    if ':' in title_upper:
        possible = title_upper.split(':', 1)[0].strip()
        if 2 <= len(possible) <= 5 and possible.isalnum():
            return possible
    
    # Method 2: Look for ASX: pattern
    m = re.search(r"\bASX\s*[:\-]?\s*([A-Z0-9]{2,5})\b", title_upper)
    if m:
        return m.group(1)
    
    # Method 3: Look for ticker in watchlist within title
    for ticker in WATCHLIST:
        if ticker in title_upper:
            return ticker
    
    return None

# --- Priority detection ---
def detect_priority(entry):
    title = entry.title.lower()
    if any(k in title for k in ["profit", "loss", "eps", "earnings", "revenue", "net income"]):
        return "💰 Earnings"
    if any(k in title for k in ["dividend", "drp", "franking", "payout"]):
        return "🟢 Dividend"
    if any(k in title for k in ["guidance", "outlook", "forecast", "fy", "full year", "h1", "h2"]):
        return "📈 Guidance"
    if any(k in title for k in ["takeover", "acquisition", "merger", "scheme"]):
        return "🎯 M&A"
    if any(k in title for k in ["trading halt", "suspension"]):
        return "⚠️ Halt"
    if any(k in title for k in ["capital raising", "placement", "spp", "rights issue"]):
        return "💵 Capital"
    return None

# --- Discord posting ---
def post_to_discord(entry, ticker):
    priority = detect_priority(entry)
    published = getattr(entry, 'published', getattr(entry, 'updated', 'N/A'))
    
    if priority:
        content = f"{priority} 📣 **{ticker}** • {published}\n{entry.title}\n{entry.link}"
    else:
        content = f"📣 **{ticker}** • {published}\n{entry.title}\n{entry.link}"
    
    try:
        resp = requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
        if resp.status_code not in (200, 204):
            logging.error(f"Failed to post: {resp.status_code} {resp.text}")
        else:
            logging.info(f"Posted to Discord: {ticker} - {entry.title}")
    except Exception as e:
        logging.error(f"Exception posting: {e}")

def post_to_discord_change(message):
    try:
        resp = requests.post(WEBHOOK_URL, json={"content": message}, timeout=10)
        if resp.status_code not in (200, 204):
            logging.error(f"Failed to post change: {resp.status_code} {resp.text}")
        else:
            logging.debug(f"Posted change notification: {message}")
    except Exception as e:
        logging.error(f"Exception posting change: {e}")

def post_startup_message(bot_name):
    try:
        content = f"✅ {bot_name} started and monitoring RSS feeds for watchlist stocks."
        requests.post(WEBHOOK_URL, json={"content": content}, timeout=10)
        logging.info(f"{bot_name} startup message posted.")
    except Exception as e:
        logging.error(f"Exception posting startup message: {e}")

# --- DB maintenance ---
def prune_db():
    cutoff = datetime.utcnow() - timedelta(days=PRUNE_DAYS)
    cur.execute("DELETE FROM seen WHERE timestamp < ?", (cutoff,))
    conn.commit()
    logging.debug("Pruned old entries from DB.")

def check_watchlist_changes():
    global WATCHLIST
    old_set = set(row[0] for row in cur.execute("SELECT ticker FROM watchlist_snapshot"))
    new_set = set(load_watchlist())
    WATCHLIST = list(new_set)

    added = new_set - old_set
    removed = old_set - new_set

    for ticker in added:
        post_to_discord_change(f"✅ Added to watchlist: {ticker}")
    for ticker in removed:
        post_to_discord_change(f"❌ Removed from watchlist: {ticker}")

    cur.execute("DELETE FROM watchlist_snapshot")
    for ticker in new_set:
        cur.execute("INSERT INTO watchlist_snapshot(ticker) VALUES(?)", (ticker,))
    conn.commit()
    logging.debug(f"Watchlist changes processed. Added: {added}, Removed: {removed}")

# --- Feed processing ---
def fetch_feeds():
    """Fetch articles from multiple RSS feeds and post watchlist items"""
    try:
        new_count = 0
        for rss_url in FEEDS:
            try:
                feed = feedparser.parse(rss_url)
                if getattr(feed, 'bozo', 0):
                    logging.debug(f"Parse issue for {rss_url}: {getattr(feed, 'bozo_exception', 'unknown error')}")
                    continue
                
                for entry in feed.entries[:50]:  # Limit to recent entries
                    try:
                        title = getattr(entry, 'title', '').strip()
                        link = getattr(entry, 'link', '').strip()
                        unique_id = getattr(entry, 'id', link or title)

                        if not title:
                            continue

                        # Extract ticker from title
                        ticker = extract_ticker(title)
                        
                        # Only process if ticker is in our watchlist
                        if ticker and ticker in WATCHLIST:
                            ann_id = f"{rss_url}_{ticker}_{unique_id}"
                            if not cur.execute("SELECT 1 FROM seen WHERE id=?", (ann_id,)).fetchone():
                                post_to_discord(entry, ticker)
                                cur.execute("INSERT INTO seen(id, timestamp) VALUES(?, ?)", (ann_id, datetime.utcnow()))
                                new_count += 1
                                time.sleep(0.2)  # Rate limiting
                    except Exception as e:
                        logging.debug(f"Error processing entry from {rss_url}: {e}")
                        continue
                        
            except Exception as e:
                logging.error(f"Error fetching {rss_url}: {e}")
                continue

        if new_count > 0:
            logging.info(f"Posted {new_count} new watchlist announcements from RSS feeds")
            conn.commit()

        prune_db()
    except Exception as e:
        logging.error(f"Error fetching feeds: {e}")

# --- Main loop ---
if __name__ == "__main__":
    logging.info("Watchlist Bot started (RSS feeds).")
    post_startup_message("Watchlist Bot")
    
    # Initial fetch
    fetch_feeds()
    
    while True:
        check_watchlist_changes()
        fetch_feeds()
        time.sleep(POLL_INTERVAL)

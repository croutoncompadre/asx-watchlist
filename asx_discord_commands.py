#!/usr/bin/env python3
import discord
from discord import app_commands
import os
import logging
import yaml
import re

# --- Logging ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Environment ---
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("DISCORD_GUILD_ID")  # AS int string
CONFIG_PATH = os.getenv("CONFIG_PATH", "/app/config.yaml")

# --- Load and save config ---
def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

def save_config(config):
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

def load_watchlist():
    config = load_config()
    return config.get("watchlist", [])

def save_watchlist(watchlist):
    config = load_config()
    config["watchlist"] = watchlist
    save_config(config)

# --- Validate ticker format ---
def validate_ticker(ticker):
    """Validate ASX ticker format (2-5 alphanumeric characters)"""
    if not ticker:
        return False, "Ticker cannot be empty"
    
    ticker = ticker.upper().strip()
    
    if not re.match(r'^[A-Z0-9]{2,5}$', ticker):
        return False, "Ticker must be 2-5 alphanumeric characters (e.g., CSL, ANZ, BHP)"
    
    return True, ticker

# --- Discord client ---
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# --- Slash commands ---
@tree.command(name="watching", description="See what tickers are currently in the watchlist")
async def watching(interaction: discord.Interaction):
    watchlist = load_watchlist()
    if watchlist:
        # Create a bullet list
        response = "📋 Current watchlist:\n" + "\n".join(f"• {ticker}" for ticker in watchlist)
    else:
        response = "⚠️ Watchlist is empty."
    await interaction.response.send_message(response)
    logging.info(f"/watching invoked by {interaction.user}. Responded with:\n{response}")

@tree.command(name="add", description="Add a ticker to the watchlist")
async def add_ticker(interaction: discord.Interaction, ticker: str):
    # Validate ticker format
    is_valid, result = validate_ticker(ticker)
    if not is_valid:
        await interaction.response.send_message(f"❌ {result}")
        return
    
    ticker = result  # Use the validated/uppercase version
    watchlist = load_watchlist()
    
    if ticker in watchlist:
        await interaction.response.send_message(f"⚠️ {ticker} is already in the watchlist.")
        return
    
    # Add to watchlist
    watchlist.append(ticker)
    save_watchlist(watchlist)
    
    response = f"✅ Added {ticker} to watchlist.\n\n📋 Current watchlist:\n" + "\n".join(f"• {t}" for t in watchlist)
    await interaction.response.send_message(response)
    logging.info(f"/add {ticker} invoked by {interaction.user}")

@tree.command(name="remove", description="Remove a ticker from the watchlist")
async def remove_ticker(interaction: discord.Interaction, ticker: str):
    # Validate ticker format
    is_valid, result = validate_ticker(ticker)
    if not is_valid:
        await interaction.response.send_message(f"❌ {result}")
        return
    
    ticker = result  # Use the validated/uppercase version
    watchlist = load_watchlist()
    
    if ticker not in watchlist:
        await interaction.response.send_message(f"⚠️ {ticker} is not in the watchlist.")
        return
    
    # Remove from watchlist
    watchlist.remove(ticker)
    save_watchlist(watchlist)
    
    if watchlist:
        response = f"✅ Removed {ticker} from watchlist.\n\n📋 Current watchlist:\n" + "\n".join(f"• {t}" for t in watchlist)
    else:
        response = f"✅ Removed {ticker} from watchlist.\n\n⚠️ Watchlist is now empty."
    
    await interaction.response.send_message(response)
    logging.info(f"/remove {ticker} invoked by {interaction.user}")

@tree.command(name="clear_tickers", description="Clear all tickers from the watchlist")
async def clear_watchlist(interaction: discord.Interaction):
    watchlist = load_watchlist()
    
    if not watchlist:
        await interaction.response.send_message("⚠️ Watchlist is already empty.")
        return
    
    # Clear watchlist
    save_watchlist([])
    
    response = f"🗑️ Cleared watchlist. Removed {len(watchlist)} ticker(s):\n" + "\n".join(f"• {ticker}" for ticker in watchlist)
    await interaction.response.send_message(response)
    logging.info(f"/clear_tickers invoked by {interaction.user}. Removed {len(watchlist)} tickers")

# --- on_ready event ---
@client.event
async def on_ready():
    await tree.sync()
    logging.info(f"Discord bot ready. Logged in as {client.user}")

# --- Run ---
client.run(TOKEN)

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
    
    embed = discord.Embed(
        title="📋 ASX Watchlist",
        description="Currently monitoring these stocks for announcements",
        color=0x00ff00 if watchlist else 0xffa500  # Green if has items, orange if empty
    )
    
    if watchlist:
        # Create a formatted list with emojis
        ticker_list = "\n".join(f"🔸 **{ticker}**" for ticker in watchlist)
        embed.add_field(
            name=f"📊 Watching {len(watchlist)} Stock(s)",
            value=ticker_list,
            inline=False
        )
        embed.set_footer(text="💡 Use /add to add more stocks • /remove to remove stocks")
    else:
        embed.add_field(
            name="⚠️ Empty Watchlist",
            value="No stocks are currently being monitored.\nUse `/add <ticker>` to add your first stock!",
            inline=False
        )
        embed.set_footer(text="💡 Try /add CSL to get started")
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/📈.png")
    await interaction.response.send_message(embed=embed)
    logging.info(f"/watching invoked by {interaction.user}")

@tree.command(name="add", description="Add a ticker to the watchlist")
async def add_ticker(interaction: discord.Interaction, ticker: str):
    # Validate ticker format
    is_valid, result = validate_ticker(ticker)
    if not is_valid:
        embed = discord.Embed(
            title="❌ Invalid Ticker Format",
            description=result,
            color=0xff0000  # Red for error
        )
        embed.add_field(
            name="📝 Valid Format",
            value="• 2-5 alphanumeric characters\n• Examples: CSL, ANZ, BHP, WBC",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
        return
    
    ticker = result  # Use the validated/uppercase version
    watchlist = load_watchlist()
    
    if ticker in watchlist:
        embed = discord.Embed(
            title="⚠️ Already in Watchlist",
            description=f"**{ticker}** is already being monitored.",
            color=0xffa500  # Orange for warning
        )
        embed.add_field(
            name="📋 Current Watchlist",
            value="\n".join(f"🔸 **{t}**" for t in watchlist),
            inline=False
        )
        await interaction.response.send_message(embed=embed)
        return
    
    # Add to watchlist
    watchlist.append(ticker)
    save_watchlist(watchlist)
    
    embed = discord.Embed(
        title="✅ Stock Added Successfully",
        description=f"**{ticker}** has been added to your watchlist!",
        color=0x00ff00  # Green for success
    )
    embed.add_field(
        name=f"📊 Now Watching {len(watchlist)} Stock(s)",
        value="\n".join(f"🔸 **{t}**" for t in watchlist),
        inline=False
    )
    embed.set_footer(text="🎯 You'll now receive announcements for this stock")
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/✅.png")
    
    await interaction.response.send_message(embed=embed)
    logging.info(f"/add {ticker} invoked by {interaction.user}")

@tree.command(name="remove", description="Remove a ticker from the watchlist")
async def remove_ticker(interaction: discord.Interaction, ticker: str):
    # Validate ticker format
    is_valid, result = validate_ticker(ticker)
    if not is_valid:
        embed = discord.Embed(
            title="❌ Invalid Ticker Format",
            description=result,
            color=0xff0000  # Red for error
        )
        embed.add_field(
            name="📝 Valid Format",
            value="• 2-5 alphanumeric characters\n• Examples: CSL, ANZ, BHP, WBC",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
        return
    
    ticker = result  # Use the validated/uppercase version
    watchlist = load_watchlist()
    
    if ticker not in watchlist:
        embed = discord.Embed(
            title="⚠️ Not in Watchlist",
            description=f"**{ticker}** is not currently being monitored.",
            color=0xffa500  # Orange for warning
        )
        embed.add_field(
            name="📋 Current Watchlist",
            value="\n".join(f"🔸 **{t}**" for t in watchlist) if watchlist else "No stocks in watchlist",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
        return
    
    # Remove from watchlist
    watchlist.remove(ticker)
    save_watchlist(watchlist)
    
    embed = discord.Embed(
        title="✅ Stock Removed Successfully",
        description=f"**{ticker}** has been removed from your watchlist.",
        color=0x00ff00  # Green for success
    )
    
    if watchlist:
        embed.add_field(
            name=f"📊 Still Watching {len(watchlist)} Stock(s)",
            value="\n".join(f"🔸 **{t}**" for t in watchlist),
            inline=False
        )
        embed.set_footer(text="🎯 You'll no longer receive announcements for this stock")
    else:
        embed.add_field(
            name="⚠️ Watchlist is Now Empty",
            value="No stocks are currently being monitored.\nUse `/add <ticker>` to add stocks back!",
            inline=False
        )
        embed.set_footer(text="💡 Try /add CSL to get started again")
    
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/🗑️.png")
    
    await interaction.response.send_message(embed=embed)
    logging.info(f"/remove {ticker} invoked by {interaction.user}")

@tree.command(name="clear_tickers", description="Clear all tickers from the watchlist")
async def clear_watchlist(interaction: discord.Interaction):
    watchlist = load_watchlist()
    
    if not watchlist:
        embed = discord.Embed(
            title="⚠️ Watchlist Already Empty",
            description="There are no stocks to clear from the watchlist.",
            color=0xffa500  # Orange for warning
        )
        embed.add_field(
            name="💡 Get Started",
            value="Use `/add <ticker>` to add your first stock!",
            inline=False
        )
        await interaction.response.send_message(embed=embed)
        return
    
    # Clear watchlist
    removed_tickers = watchlist.copy()
    save_watchlist([])
    
    embed = discord.Embed(
        title="🗑️ Watchlist Cleared",
        description=f"Removed **{len(removed_tickers)}** stock(s) from your watchlist.",
        color=0xff6b6b  # Light red for clearing
    )
    embed.add_field(
        name="📋 Removed Stocks",
        value="\n".join(f"🔸 **{ticker}**" for ticker in removed_tickers),
        inline=False
    )
    embed.add_field(
        name="💡 Next Steps",
        value="Use `/add <ticker>` to add stocks back to your watchlist!",
        inline=False
    )
    embed.set_footer(text="🎯 You'll no longer receive any stock announcements")
    embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/🗑️.png")
    
    await interaction.response.send_message(embed=embed)
    logging.info(f"/clear_tickers invoked by {interaction.user}. Removed {len(removed_tickers)} tickers")

# --- on_ready event ---
@client.event
async def on_ready():
    await tree.sync()
    logging.info(f"Discord bot ready. Logged in as {client.user}")

# --- Run ---
client.run(TOKEN)

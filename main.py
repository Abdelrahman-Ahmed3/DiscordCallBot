import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json
import webserver
import asyncio
import requests
import threading

load_dotenv()
token = os.getenv('DISCORD_TOKEN')
JSONBIN_API_KEY = os.getenv('JSONBIN_API_KEY')
JSONBIN_BIN_ID = os.getenv('JSONBIN_BIN_ID')

if not all([token, JSONBIN_API_KEY, JSONBIN_BIN_ID]): #checks if anything is missing and raises an error in that case
    print("❌ FATAL ERROR: One or more required environment variables are missing.")
    exit()

JSONBIN_URL = f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}"
HEADERS = {
    'Content-Type': 'application/json',
    'X-Master-Key': JSONBIN_API_KEY
}

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.presences = True
intents.message_content = True
intents.voice_states = True
intents.members = True
intents.reactions = True

bot = commands.Bot(command_prefix='!', intents=intents)
pending_notifications = set()

def load_config():
    default_config = {
        "waiting_channelid": None,
        "target_channelid": None,
        "targets": [],
        "optin_message_id": None,
        "wait": 10,
        "server_id": None
    }
    try:
        # Fetch the latest version of the bin
        response = requests.get(f"{JSONBIN_URL}/latest", headers=HEADERS)
        response.raise_for_status() # Raises an error for bad responses (4xx or 5xx)
        return response.json()['record']
    except (requests.exceptions.RequestException, json.JSONDecodeError, KeyError) as e:
        print(f"Failed to load config from jsonbin.io: {e}. Using default config.")
        # If it fails (e.g., first run), save the default config to create the bin content
        save_config(default_config)
        return default_config

def save_config(config_data):
    try:
        response = requests.put(JSONBIN_URL, json=config_data, headers=HEADERS)
        response.raise_for_status() # Check for errors
        print("Configuration successfully saved to jsonbin.io.")
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to save config to jsonbin.io: {e}")
config = load_config()
print("Loaded config from JSONBin:", config)

@bot.event #happens when the bot boots up, needed.
async def on_ready():
    server_id = config.get("server_id")
    if server_id:
        try:
            guild = discord.Object(id=server_id)
            bot.tree.copy_global_to_guild(guild=guild)
            await bot.tree.sync(guild=guild)
            print(f"Commands have been forcefully synced to server: {server_id}")
        except Exception as e:
            print(f"Error during command sync: {e}")
    else:
        print("--------------------------------------------------")
        print("WARNING: Server ID is not set in the config.")
        print("An admin must run the /set_server command.")
        print("--------------------------------------------------")
    print(f" {bot.user.name} set up successfully with {len(config.get('targets', []))} members")


# Keep Render alive and run bot in separate thread
webserver.keep_alive()
threading.Thread(target=lambda: bot.run(token, log_handler=handler, log_level=logging.DEBUG)).start()

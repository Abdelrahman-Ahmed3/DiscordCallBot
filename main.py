import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json
import webserver
import asyncio
import requests

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
        "wait": 10
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

@bot.event #happens when the bot boots up, needed.
async def on_ready():
    print(f" {bot.user.name} set up successfully with {len(config["targets"])} members")

@bot.tree.command(name="set_waiting_channel")
@discord.app_commands.checks.has_permissions(administrator=True)
async def set_waiting_channel(interaction: discord.Interaction, WaitingChannel: discord.VoiceChannel):#function to add the waiting channel from discord
    try:
        config["waiting_channelid"] = WaitingChannel.id
        save_config(config)
        await interaction.response.send_message(f"✅ Waiting channel updated to {WaitingChannel.name}")
    except Exception as e:
        print(f"Error with waiting channel: {e}")
        await interaction.response.send_message("❌ Failed to update waiting channel.", ephemeral=True)


@bot.tree.command(name="set_target_channel")
@discord.app_commands.checks.has_permissions(administrator=True)
async def set_target_channel(interaction: discord.Interaction, TargetChannel: discord.VoiceChannel): #function to add the Target channel from discord
    try:
        config["target_channelid"] = TargetChannel.id
        save_config(config)
        await interaction.response.send_message(f"✅ Target channel updated to {TargetChannel.name}")
    except Exception as e:
        print(f"Error with target channel: {e}")
        await interaction.response.send_message("❌ Failed to update target channel.", ephemeral=True)

@bot.tree.command(name="set_waiting_time")
@discord.app_commands.checks.has_permissions(administrator=True)
async def set_waiting_time(interaction: discord.Interaction, WaitTime: int): #function to configure the waiting time from discord
    try:
        config["wait"] = WaitTime
        save_config(config)
        await interaction.response.send_message(f"✅ Waiting time updated to `{WaitTime}` seconds")
    except Exception as e:
        print(f"Error with waiting channel: {e}")
        await interaction.response.send_message("❌ Failed to update waiting time.", ephemeral=True)

@bot.tree.command(name="setup_message")
@discord.app_commands.checks.has_permissions(administrator=True)
async def setup_message(interaction: discord.Interaction): #/setup_message sends an embed with two reactions to monitor in the next event for adding people to the .json file
    embed = discord.Embed(
        title="Voice Notification Opt-in",
        description="React with ✅ to get notified when someone is waiting.\nReact with ❌ to stop notifications.",
        color=discord.Color.blue()
    )
    msg = await interaction.channel.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    config["optin_message_id"] = msg.id
    save_config(config)

@bot.tree.command(name="config")
@discord.app_commands.checks.has_permissions(administrator=True)
async def cfg(interaction: discord.Interaction): #/config send a message with the full config
    config_dump = json.dumps(config, indent=4)
    await interaction.response.send_message(f"```json\n{config_dump}\n```", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after): #checks if any member joins the waiting channel with the target role and then moves them to target channel
    if not config['waiting_channelid'] or not config['target_channelid']: # Do nothing if the channels are not configured yet to avoid the bot crashing
        return

    waiting_channel = member.guild.get_channel(config['waiting_channelid'])
    target_channel = member.guild.get_channel(config['target_channelid'])

    if waiting_channel.members and len(waiting_channel.members) > 1: #checks if the channel has more than one member and if the channel does it moves them all to the target channel
        print ("len check good")
        for waiting_member in list(waiting_channel.members):
            try:
                await waiting_member.move_to(target_channel)
            except discord.Forbidden:
                print("Missing Move Members permission")
            except Exception as e:
                print("Move error:", e)

    if after.channel and after.channel.id == config["waiting_channelid"] and before.channel != after.channel:
        print("waiting good")
        user_id = member.id
        if user_id in pending_notifications:
            print("user already pending a notification")
            return
        pending_notifications.add(user_id)
        try:
            await asyncio.sleep(config.get('wait',10))  # this and the next if statement waits the wait time and then checks if the person is still in the channel to prevent fast spamming
            waiting_channel = member.guild.get_channel(config['waiting_channelid'])

            # recheck conditions after the wait
            if (
                    user_id in config["targets"]
                    and member.voice
                    and member.voice.channel
                    and member.voice.channel.id == config["waiting_channelid"]  # still in waiting channel
                    and len(waiting_channel.members) <= 1
            ):
                print("user id good")
                if user_id in config["targets"] and len(waiting_channel.members) <= 1 :
                    print("user id good")
                    for targetid in config["targets"]: #goes through the target members list and sends them a dm
                         print("for loop (1) good")
                         if targetid != member.id:
                             try: #try/except block to prevent the bot from not completing the list if someone blocked it or has dms closed
                                user = await bot.fetch_user(targetid)
                                await user.send(f"<@{user_id}> is now waiting for you in <#{config['waiting_channelid']}>")
                             except discord.Forbidden:
                                 print(f"Could not DM {targetid}: DMs disabled or bot blocked")
                             except discord.NotFound:
                                 print(f"User {targetid} not found")
                             except discord.HTTPException as e:
                                 print(f"Failed to send DM to {targetid}: {e}")
        finally:
           pending_notifications.discard(user_id)

@bot.event
async def on_raw_reaction_add(payload): #adds and removes members from the setup message
    try:
            print(f"[REACTION] user={payload.user_id}, emoji={payload.emoji}, message={payload.message_id}")
            if payload.user_id == bot.user.id: #avoids the bot's id from getting added
                print("bot reaction detected")
                return

            if payload.message_id != config["optin_message_id"]: #checks if the optin message is the one with the reaction event
                print(f"reaction on the non opt in message, opt:{payload.message_id}, msg:{config['optin_message_id']}")
                return

            if str(payload.emoji) == "✅": #adds members when they react
                print("✅ reaction detected")
                if payload.user_id not in config["targets"]:
                    config["targets"].append(payload.user_id)
                    save_config(config)
                    user = await bot.fetch_user(payload.user_id)
                    await user.send("You have successfully been added to the list")
                    print(f"<{payload.user_id}> successfully saved to the list")
                else:
                    user = await bot.fetch_user(payload.user_id)
                    await user.send("You are already in the list")
                    print(f"{payload.user_id} is already in the targets list")

            if str(payload.emoji) == "❌": #removes members by reaction
                if payload.user_id in config["targets"]:
                    config["targets"].remove(payload.user_id)
                    save_config(config)
                    user = await bot.fetch_user(payload.user_id)
                    await user.send("You have successfully been removed from the list")
                    print(f"<{payload.user_id}> deleted from targets")
                else:
                    user = await bot.fetch_user(payload.user_id)
                    await user.send("You are not in the list")
                    print(f"<{payload.user_id}> is not in targets")

    except Exception:
        import traceback
        traceback.print_exc()

webserver.keep_alive()
bot.run(token, log_handler=handler, log_level=logging.DEBUG)

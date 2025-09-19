import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json
import webserver
import asyncio
load_dotenv()
token = os.getenv('DISCORD_TOKEN')

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
        with open("config.json", "r") as f:
            return json.load(f)   # load as dict
    except (FileNotFoundError, json.JSONDecodeError):
        save_config(default_config) # default values
        return default_config

def save_config(config):
    with open("config.json", "w") as f:
        json.dump(config, f, indent=4)
config = load_config()

@bot.event #happens when the bot boots up, needed.
async def on_ready():
    print(f" {bot.user.name} set up successfully with {len(config["targets"])} members")

@bot.command()
async def wchannel(ctx, *, wchannel: int):#function to add the waiting channel from discord
    try:
        config["waiting_channelid"] = wchannel
        save_config(config)
        await ctx.send(f"✅ Waiting channel updated to `{wchannel}`")
    except:
        print("error with waiting channel")


@bot.command()
async def tchannel(ctx, *, tchannel: int): #function to add the target channel from discord
    try:
        config["target_channelid"] = tchannel
        save_config(config)
        await ctx.send(f"✅ Waiting channel updated to `{tchannel}`")
    except:
        print("error with target channel")

@bot.command()
async def wait (ctx, *, waittime: int):#function to add the waiting channel from discord
    try:
        config["wait"] = waittime
        save_config(config)
        await ctx.send(f"✅ Waiting time updated to `{waittime}` seconds")
    except:
        print("error with waiting time")

@bot.command()
async def setup(ctx): #!setup sends an embed with two reactions to monitor in the next event for adding people to the .json file
    embed = discord.Embed(
        title="Voice Notification Opt-in",
        description="React with ✅ to get notified when someone is waiting.\nReact with ❌ to stop notifications.",
        color=discord.Color.blue()
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    config["optin_message_id"] = msg.id
    save_config(config)


@bot.event
async def on_voice_state_update(member, before, after): #checks if any member joins the waiting channel with the target role and then moves them to target channel
    waiting_channel = member.guild.get_channel(config['waiting_channelid'])
    target_channel = member.guild.get_channel(config['target_channelid'])
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
    if waiting_channel.members and len(waiting_channel.members) > 1: #checks if the channel has more than one member and if the channel does it moves them all to the target channel
        print ("len check good")
        for waiting_member in list(waiting_channel.members):
            try:
                await waiting_member.move_to(target_channel)
            except discord.Forbidden:
                print("Missing Move Members permission")
            except Exception as e:
                print("Move error:", e)

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

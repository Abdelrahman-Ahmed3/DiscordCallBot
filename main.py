import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os
import json

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

#CONFIGURE THIS
waiting_channelid = 1410768045231702077 #this is the channel that people wait in
target_channelid = 762150180409180170 #this is the channel that they get moved to after someone joins
def load_targets(): #reads the .json file with the member list
    try:
        with open("targets.json", "r") as f:
            return set(json.load(f))   # IDs in a Python set
    except (FileNotFoundError, json.JSONDecodeError):
        return set()   # start empty if file doesn’t exist or is broken

def save_targets(targets): #saves the targets to the .json
    with open("targets.json", "w") as f:
        json.dump(list(targets), f)  # save IDs back to JSON
target_members = load_targets()

@bot.event #happens when the bot boots up, needed.
async def on_ready():
    print(f" {bot.user.name} set up successfully with {len(target_members)} members")

@bot.command()
async def setup_optin(ctx):
    embed = discord.Embed(
        title="Voice Notification Opt-in",
        description="React with ✅ to get notified when someone is waiting.\nReact with ❌ to stop notifications.",
        color=discord.Color.blue()
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    with open("optinmessageid.json", "w") as f:
        json.dump(ctx.message.id, f)


@bot.event
async def on_voice_state_update(member, before, after): #checks if any member joins the waiting channel with the target role and then moves them to target channel
    if before.channel is None and after.channel is not None: #checks if anyone joined the channel
        if after.channel.id == waiting_channelid:
            print("waiting good")
            user_id = member.id
            if user_id in target_members:
                print("user id good")
                for targetid in target_members: #goes through the target members list and sends them a dm
                     print("for loop (1) good")
                     if targetid != member.id:
                        user = await bot.fetch_user(targetid)
                        await user.send(f"<@{user_id}> is now waiting for you in the voice channel!")
                     else:
                         continue
    waiting_channel = member.guild.get_channel(waiting_channelid)
    target_channel = member.guild.get_channel(target_channelid)
    if waiting_channel.members and len(waiting_channel.members) > 1: #checks if the channel has more than one member and if the channel does it moves them all to the target channel
        print ("len check good")
        for waiting_member in list(waiting_channel.members):
            try:
                await waiting_member.move_to(target_channel)
            except discord.Forbidden:
                print("Missing Move Members permission")
            except Exception as e:
                print("Move error:", e)

@bot.command
async def setup_optin(ctx): #!setup_optin sends an embed with two reactions to monitor in the next event for adding people to the .json file
    embed = discord.Embed(
        title="Voice Notification Opt-in",
        description="React with ✅ to get notified when someone is waiting.\nReact with ❌ to stop notifications.",
        color=discord.Color.blue()
    )
    msg = await ctx.send(embed=embed)
    await msg.add_reaction("✅")
    await msg.add_reaction("❌")
    # save message ID to a file so we can use it later
    with open("optin.json", "w") as f:
        json.dump({"optin_message_id": msg.id}, f)


@bot.event
async def on_raw_reaction_add(payload):
    try:
        print("RAW REACTION EVENT FIRED")
        print("payload:", payload)
        print("guild:", payload.guild_id,
              "channel:", payload.channel_id,
              "message:", payload.message_id,
              "user:", payload.user_id,
              "emoji:", payload.emoji)
    except Exception:
        import traceback
        traceback.print_exc()



@bot.event
async def on_raw_reaction_add(payload):
    print("Reaction detected:", payload.emoji, "from", payload.user_id)
    with open("optin.json", "r") as f:
        optin_message_id = json.load(f)["optinmessageid"]
    with open("targets.json", "r") as f:
        data = json.load(f)
    # ignore the bot's own reactions
    #if payload.user_id == bot.user.id:
        #return
    # check it's the optin message

    #if payload.message_id != int(optin_message_id):
        #print("Payload message:", payload.message_id, "Opt-in message:", optin_message_id)
        #return
    if str(payload.emoji) == "✅":
        print("Reaction detected:", payload.emoji, "from", payload.user_id)
        if payload.user_id not in data["targets"]:  # avoid duplicates
            print("check for not in data works")
            data["targets"].append(payload.user_id)
            with open ("targets.json", "w") as f:
                print("Updated targets:", data)
                json.dump(data, f)

    elif str(payload.emoji) == "❌":
        if payload.user_id in data["targets"]:
            data["targets"].remove(payload.user_id)
            with open ("targets.json", "w") as f:
                json.dump(data, f)


bot.run(token, log_handler=handler, log_level=logging.DEBUG)
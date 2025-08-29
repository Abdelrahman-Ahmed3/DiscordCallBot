import discord
from discord.ext import commands
import logging
from dotenv import load_dotenv
import os

load_dotenv()
token = os.getenv('DISCORD_TOKEN')

handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
intents = discord.Intents.default()
intents.presences = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

#CONFIGURE THIS
waiting_channelid = "1410768045231702077" #this is the channel that people wait in
target_channelid = "762150180409180170" #this is the channel that they get moved to after someone joins
target_members = (269533967114305537, 693794100503248937) #these are the members that will get notified

@bot.event #happens when the bot boots up, needed.
async def on_ready():
    print(f" {bot.user.name} set up successfully")

@bot.event
async def on_voice_state_update(member, before, after): #checks if any member joins the waiting channel with the target role and then moves them to target channel
    if before.channel is None and after.channel is not None:
        if after.channel.id == waiting_channelid:
            user_id = member.id
            if user_id in target_members:



bot.run(token, log_handler=handler, log_level=logging.DEBUG)
import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
  
load_dotenv() 
from dotenv import dotenv_values
config = dotenv_values(".env")

from help_cog import help_cog
from music_cog import music_cog

if not discord.opus.is_loaded():
    discord.opus.load_opus('libopus.so.0')	

intents = discord.Intents.all()

bot = commands.Bot(command_prefix="/", intents=intents)

@bot.event
async def on_ready():
    bot.remove_command("help")
    await bot.add_cog(music_cog(bot))
    await bot.add_cog(help_cog(bot))
    print("The bot is online!")

@bot.command()
async def hello(ctx):
    await ctx.send("Hello")

@bot.command()
async def test(ctx):
    await ctx.send("Test")

bot.run(config['DISCORD_SECRET_KEY'])
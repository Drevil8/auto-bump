import discord
from discord.ext import commands
import os
from web_automation import run_web_task

# Load bot token from environment variable
TOKEN = os.environ.get("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command(name="run")
async def run_task(ctx):
    """Triggers the web automation task."""
    await ctx.send("Starting the web task... please wait.")
    try:
        result = await run_web_task()
        await ctx.send(f"Done! Result: {result}")
    except Exception as e:
        await ctx.send(f"Something went wrong: {e}")

bot.run(TOKEN)

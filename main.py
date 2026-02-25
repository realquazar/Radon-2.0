import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

intents = nextcord.Intents.default()
intents.members = True  
intents.message_content = True 

activity = nextcord.Game(name="Try /startworkout")

bot = commands.Bot(
    intents=intents, 
    activity=activity
)

COGS_DIR = "cogs"

if __name__ == "__main__":
    for filename in os.listdir(f"./{COGS_DIR}"):
        if filename.endswith(".py"):
            try:
                bot.load_extension(f"{COGS_DIR}.{filename[:-3]}")
                print(f"✅ Loaded: {filename}")
            except Exception as e:
                print(f"❌ Failed to load {filename}: {e}")

@bot.event
async def on_ready():
    print("---")
    print(f"🛡️ Radon 2.0 is Online")
    print(f"Logged in as: {bot.user.name}")
    print(f"Status: Playing {bot.activity.name}")
    print("---")

bot.run(os.getenv("DISCORD_TOKEN"))
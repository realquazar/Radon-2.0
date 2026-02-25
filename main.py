import nextcord
from nextcord.ext import commands
import os
from dotenv import load_dotenv

load_dotenv()

# 1. Setup Intents
intents = nextcord.Intents.default()
intents.members = True  
intents.message_content = True 

# 2. Initialize Bot with Activity
# We define the activity here so it shows up the second the bot logs in
activity = nextcord.Game(name="Try /startworkout")

bot = commands.Bot(
    intents=intents, 
    activity=activity
)

# 3. Load Cogs Automatically
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

# 4. Start the Bot
bot.run(os.getenv("DISCORD_TOKEN"))
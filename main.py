import os
from dotenv import load_dotenv
import discord
from discord.ext import commands
from pymongo import MongoClient
import time

# Load environment variables from .env file
load_dotenv()

# Get the token and MongoDB URI from the environment variables
TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI')

# Set up the MongoDB client
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['discord']  # Access the 'discord' database

# Store the start time
start_time = time.time()

# Set up the intents
intents = discord.Intents.all()

# Create a bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="people crashout in realtime"))
    bot.uptime = time.time() - start_time
    print(f'We have logged in as {bot.user}')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"Error syncing commands: {e}")
    print("Cogs loaded:", bot.cogs.keys())  # Lists all loaded cogs
    print("Commands loaded:", bot.tree.get_commands())  # Lists all slash commands

# Load commands from the commands directory
@bot.event
async def setup_hook():
    bot.db = db  # Attach the database to the bot instance
    await bot.load_extension('commands.coinflip')
    await bot.load_extension('commands.setbalance')
    await bot.load_extension('commands.baltop')
    await bot.load_extension('commands.avatar')
    await bot.load_extension('commands.help')
    await bot.load_extension('commands.banner')
    await bot.load_extension('commands.reaction_tracker')
    await bot.load_extension('commands.give')
    await bot.load_extension('commands.balance')
    await bot.load_extension('commands.roll')
    await bot.load_extension('commands.losstop')
    await bot.load_extension('commands.shop')
    await bot.load_extension('commands.avatar_tracker')
    await bot.load_extension('commands.status_tracker')
    await bot.load_extension('commands.activity_tracker')

# Run the bot
bot.run(TOKEN)

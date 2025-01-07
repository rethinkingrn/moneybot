import discord
from discord.ext import commands
from pymongo import MongoClient
from datetime import datetime
import os

class MessageTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo_url = os.getenv("MONGODB_URI")  # MongoDB connection
        mongo_client = MongoClient(mongo_url)
        self.db = mongo_client["discord"]  # Database name
        self.collection = self.db["messages"]  # Collection for storing messages
        self.ignored_channels = set()  # Set of ignored channel IDs

        # Load ignored channels from the database
        ignored_channels_data = self.db["ignored_channels"].find_one({"key": "ignored_channels"})
        if ignored_channels_data:
            self.ignored_channels = set(ignored_channels_data.get("channels", []))

    async def save_ignored_channels(self):
        """Save the ignored channels list to the database."""
        self.db["ignored_channels"].update_one(
            {"key": "ignored_channels"},
            {"$set": {"channels": list(self.ignored_channels)}},
            upsert=True
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        """Track messages and ignore those from ignored channels."""
        if message.author.bot or message.channel.id in self.ignored_channels:
            return

        log_entry = {
            "message_id": message.id,
            "author_id": message.author.id,
            "channel_id": message.channel.id,
            "content": message.content,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.collection.insert_one(log_entry)

    @commands.command(name="ignorechannel", help="Add a channel to the ignore list.")
    async def ignore_channel(self, ctx, channel: discord.TextChannel):
        """Add a channel to the ignored list."""
        if channel.id not in self.ignored_channels:
            self.ignored_channels.add(channel.id)
            await self.save_ignored_channels()
            await ctx.send(f"Channel {channel.mention} has been added to the ignore list.")
        else:
            await ctx.send(f"Channel {channel.mention} is already in the ignore list.")

    @commands.command(name="unignorechannel", help="Remove a channel from the ignore list.")
    async def unignore_channel(self, ctx, channel: discord.TextChannel):
        """Remove a channel from the ignored list."""
        if channel.id in self.ignored_channels:
            self.ignored_channels.remove(channel.id)
            await self.save_ignored_channels()
            await ctx.send(f"Channel {channel.mention} has been removed from the ignore list.")
        else:
            await ctx.send(f"Channel {channel.mention} is not in the ignore list.")

    @commands.command(name="listignoredchannels", help="List all ignored channels.")
    async def list_ignored_channels(self, ctx):
        """List all ignored channels."""
        if not self.ignored_channels:
            await ctx.send("No channels are currently ignored.")
            return

        ignored_channel_mentions = [f"<#{channel_id}>" for channel_id in self.ignored_channels]
        await ctx.send(f"Ignored Channels:\n{', '.join(ignored_channel_mentions)}")

async def setup(bot):
    await bot.add_cog(MessageTracker(bot))

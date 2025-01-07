import discord
from discord.ext import commands, tasks
from pymongo import MongoClient
import os
from datetime import datetime, timedelta
from collections import Counter
import aiohttp

class HourlyStats(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo_url = os.getenv("MONGODB_URI")  # MongoDB connection
        mongo_client = MongoClient(mongo_url)
        self.db = mongo_client["discord"]  # Database name
        self.collection = self.db["messages"]  # Collection name
        self.webhook_url = os.getenv("WEBHOOK_URL")  # Webhook URL from the .env file
        self.hourly_stats.start()  # Start the hourly stats task

    def cog_unload(self):
        """Stop the task when the cog is unloaded."""
        self.hourly_stats.cancel()

    @tasks.loop(hours=1)
    async def hourly_stats(self):
        """Task to generate and send hourly stats."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Query the MongoDB collection for messages from the last hour
        recent_messages = list(self.collection.find({"timestamp": {"$gte": one_hour_ago.isoformat()}}))

        total_messages = len(recent_messages)

        # Count messages per user
        user_message_counts = Counter(msg["author_id"] for msg in recent_messages)

        if user_message_counts:
            most_active_user_id, most_messages = user_message_counts.most_common(1)[0]
            most_active_user_name = await self.get_user_name(most_active_user_id)
        else:
            most_active_user_name = "N/A"
            most_messages = 0

        # Prepare stats embed
        embed = discord.Embed(
            title="Hourly Message Stats",
            color=discord.Color.green(),
            timestamp=now
        )
        embed.add_field(name="Total Messages", value=total_messages, inline=False)
        embed.add_field(name="Most Active User", value=f"{most_active_user_name} ({most_messages} messages)", inline=False)
        embed.set_footer(text="Stats generated automatically every hour.")

        # Send stats to the webhook
        if self.webhook_url:
            await self.send_to_webhook(embed)

    async def get_user_name(self, user_id):
        """Fetch the username of a user by ID."""
        user = self.bot.get_user(user_id)
        if not user:
            try:
                user = await self.bot.fetch_user(user_id)
            except discord.NotFound:
                return f"Unknown User ({user_id})"
        return str(user)

    async def send_to_webhook(self, embed):
        """Send the stats embed to a webhook."""
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.webhook_url, json={"embeds": [embed.to_dict()]}) as response:
                    if response.status == 204:
                        print("Hourly stats sent to webhook successfully.")
                    else:
                        print(f"Failed to send hourly stats to webhook. HTTP Status: {response.status}")
            except Exception as e:
                print(f"Failed to send hourly stats to webhook: {e}")

    def is_authorized_user(ctx):
        """Check if the user is authorized to execute the command."""
        return ctx.author.id == 183743105688797184

    @commands.command(name="hourlystats", help="Manually generate and view the last hour's stats.")
    @commands.check(is_authorized_user)
    async def hourly_stats_command(self, ctx):
        """Manually generate stats for the last hour and send them to the invoking channel."""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)

        # Query the MongoDB collection for messages from the last hour
        recent_messages = list(self.collection.find({"timestamp": {"$gte": one_hour_ago.isoformat()}}))

        total_messages = len(recent_messages)

        # Count messages per user
        user_message_counts = Counter(msg["author_id"] for msg in recent_messages)

        if user_message_counts:
            most_active_user_id, most_messages = user_message_counts.most_common(1)[0]
            most_active_user_name = await self.get_user_name(most_active_user_id)
        else:
            most_active_user_name = "N/A"
            most_messages = 0

        # Prepare stats embed
        embed = discord.Embed(
            title="Hourly Message Stats",
            color=discord.Color.green(),
            timestamp=now
        )
        embed.add_field(name="Total Messages", value=total_messages, inline=False)
        embed.add_field(name="Most Active User", value=f"{most_active_user_name} ({most_messages} messages)", inline=False)
        embed.set_footer(text="Stats generated manually.")

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(HourlyStats(bot))

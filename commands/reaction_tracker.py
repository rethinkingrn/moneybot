import discord
from discord.ext import commands
from pymongo import MongoClient

class ReactionTracker(commands.Cog):
    def __init__(self, bot, db):
        self.bot = bot
        self.db = db  # MongoDB instance passed to the cog

    @commands.command()
    async def track_reaction(self, ctx, message_id: int):
        """Adds emojis to the message for tracking reactions."""
        
        # Get the message from the channel using its ID
        try:
            message = await ctx.channel.fetch_message(message_id)
        except discord.NotFound:
            await ctx.send("Message not found.")
            return

        # Add the emojis to the message for tracking
        await message.add_reaction("💀")
        await message.add_reaction("😂")
        await message.add_reaction("🐐")
        await message.add_reaction("✅")
        await ctx.send(f"Now tracking reactions on message ID: {message_id}")

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Triggered when a reaction is added to any message."""
        
        # Ignore bot reactions
        if user.bot:
            return

        reactor_id = str(user.id)  # ID of the person reacting
        message_id = str(reaction.message.id)  # ID of the reacted message
        message_author_id = str(reaction.message.author.id)  # ID of the message author

        # Ignore reactions to their own message
        if reactor_id == message_author_id:
            return

        # Check if the user has already reacted to this message
        reactor_data = self.db.users.find_one({"user_id": reactor_id})
        if reactor_data and message_id in reactor_data.get("reacted_messages", []):
            # User has already reacted to this message; no further rewards
            return

        # Determine rewards based on the emoji
        if str(reaction.emoji) == "💀":
            self.reward_users(reactor_id, message_author_id, message_id, 200, 1000)
        elif str(reaction.emoji) == "😂":
            self.reward_users(reactor_id, message_author_id, message_id, 50, 250)
        elif str(reaction.emoji) == "🐐":
            self.reward_users(reactor_id, message_author_id, message_id, 300, 1500)
        elif str(reaction.emoji) == "✅":
            self.reward_users(reactor_id, message_author_id, message_id, 150, 750)

    def reward_users(self, reactor_id, message_author_id, message_id, reactor_reward, author_reward):
        """
        Reward the reactor and the message author.

        Args:
        - reactor_id (str): User ID of the reactor.
        - message_author_id (str): User ID of the message author.
        - message_id (str): The ID of the message being reacted to.
        - reactor_reward (int): Reward for the reactor.
        - author_reward (int): Reward for the message author.
        """
        # Reward the reactor
        reactor_data = self.db.users.find_one({"user_id": reactor_id})
        if reactor_data:
            self.db.users.update_one(
                {"user_id": reactor_id},
                {
                    "$inc": {"balance": reactor_reward},
                    "$addToSet": {"reacted_messages": message_id},  # Add the message ID to the reacted list
                }
            )
        else:
            self.db.users.insert_one({
                "user_id": reactor_id,
                "balance": reactor_reward,
                "reacted_messages": [message_id]
            })

        # Reward the message author
        author_data = self.db.users.find_one({"user_id": message_author_id})
        if author_data:
            self.db.users.update_one(
                {"user_id": message_author_id},
                {"$inc": {"balance": author_reward}}
            )
        else:
            self.db.users.insert_one({
                "user_id": message_author_id,
                "balance": author_reward,
                "reacted_messages": []
            })

# Setup the bot and load the extension
async def setup(bot):
    # Assuming bot.db is already set up with MongoDB connection
    await bot.add_cog(ReactionTracker(bot, bot.db))

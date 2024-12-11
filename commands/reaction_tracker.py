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
        message_author_id = str(reaction.message.author.id)  # ID of the message author

        # Ignore reactions to their own message
        if reactor_id == message_author_id:
            return

        # Determine rewards based on the emoji
        if str(reaction.emoji) == "💀":
            self.reward_users(reactor_id, message_author_id, 200, 1000)
            print(f"💀 reaction: User {reactor_id} reacted to message by {message_author_id}.")
        elif str(reaction.emoji) == "😂":
            self.reward_users(reactor_id, message_author_id, 50, 250)
            print(f"😂 reaction: User {reactor_id} reacted to message by {message_author_id}.")
        elif str(reaction.emoji) == "🐐":
            self.reward_users(reactor_id, message_author_id, 300, 1500)
            print(f"🐐 reaction: User {reactor_id} reacted to message by {message_author_id}.")
        elif str(reaction.emoji) == "✅":
            self.reward_users(reactor_id, message_author_id, 150, 750)
            print(f"✅ reaction: User {reactor_id} reacted to message by {message_author_id}.")

    def reward_users(self, reactor_id, message_author_id, reactor_reward, author_reward):
        """
        Reward the reactor and the message author.

        Args:
        - reactor_id (str): User ID of the reactor.
        - message_author_id (str): User ID of the message author.
        - reactor_reward (int): Reward for the reactor.
        - author_reward (int): Reward for the message author.
        """
        # Reward the reactor
        reactor_data = self.db.users.find_one({"user_id": reactor_id})
        if reactor_data:
            self.db.users.update_one(
                {"user_id": reactor_id},
                {"$inc": {"balance": reactor_reward}}
            )
        else:
            self.db.users.insert_one({
                "user_id": reactor_id,
                "balance": reactor_reward,
                "reacted_messages": []
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

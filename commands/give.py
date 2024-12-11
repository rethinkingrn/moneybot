import discord
from discord.ext import commands
from discord import app_commands

class GiveMoney(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="give", description="Give money to another user")
    @app_commands.describe(
        recipient="The user you want to give money to",
        amount="The amount of money to give"
    )
    async def give(self, interaction: discord.Interaction, recipient: discord.User, amount: int):
        sender_id = str(interaction.user.id)
        recipient_id = str(recipient.id)

        if sender_id == recipient_id:
            await interaction.response.send_message("You cannot give money to yourself!", ephemeral=True)
            return

        if amount <= 0:
            await interaction.response.send_message("You must give a positive amount!", ephemeral=True)
            return

        # Fetch sender and recipient data
        sender_data = self.bot.db['users'].find_one({"user_id": sender_id})
        recipient_data = self.bot.db['users'].find_one({"user_id": recipient_id})

        if sender_data is None:
            await interaction.response.send_message("You need to register first!", ephemeral=True)
            return

        if sender_data.get("balance", 0) < amount:
            await interaction.response.send_message("You don't have enough money to give!", ephemeral=True)
            return

        # Update balances
        new_sender_balance = sender_data["balance"] - amount
        self.bot.db['users'].update_one({"user_id": sender_id}, {"$set": {"balance": new_sender_balance}})

        if recipient_data:
            # Recipient exists in the database
            new_recipient_balance = recipient_data["balance"] + amount
            self.bot.db['users'].update_one({"user_id": recipient_id}, {"$set": {"balance": new_recipient_balance}})
        else:
            # Create recipient in the database if they don't exist
            self.bot.db['users'].insert_one({
                "user_id": recipient_id,
                "balance": amount,
                "reacted_messages": []  # Initialize with an empty reacted messages list
            })

        await interaction.response.send_message(
            f"You successfully gave **${amount}** to {recipient.mention}.\n"
            f"Your new balance is **${new_sender_balance}**."
        )

async def setup(bot):
    await bot.add_cog(GiveMoney(bot))

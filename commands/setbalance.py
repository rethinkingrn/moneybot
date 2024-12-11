import discord
from discord.ext import commands
from discord import app_commands

allowed_user_id = '183743105688797184'

class SetBalance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setbalance", description="Set the balance of a user.")
    @app_commands.describe(user="The user to set the balance for", amount="The amount to set")
    async def setbalance(self, interaction: discord.Interaction, user: discord.User, amount: int):
        if str(interaction.user.id) != allowed_user_id:
            return await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)

        try:
            user_data = self.bot.db['users'].find_one({"user_id": str(user.id)})

            if user_data is None:
                # Register the user if they don't exist
                self.bot.db['users'].insert_one({"user_id": str(user.id), "balance": amount})
            else:
                # Update the user's balance
                self.bot.db['users'].update_one({"user_id": str(user.id)}, {"$set": {"balance": amount}})

            await interaction.response.send_message(f"Just set {user.display_name}'s balance to ${amount}.")
        except Exception as error:
            print(error)
            await interaction.response.send_message("There was an error setting the balance.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(SetBalance(bot))

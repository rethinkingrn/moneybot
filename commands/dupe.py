import discord
from discord.ext import commands
from discord import app_commands
import random

class Dupe(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dupe", description="Prints your previous balance and changes your current balance randomly.")
    async def dupe(self, interaction: discord.Interaction):
        user_id = str(interaction.user.id)
        user_data = self.bot.db['users'].find_one({"userId": user_id})

        try:
            if user_data is None:
                # Register user if they don't exist
                self.bot.db['users'].insert_one({"userId": user_id, "balance": 0})
                previous_balance = 0
                await interaction.response.send_message("You have been registered with a balance of **0**.")
            else:
                previous_balance = user_data.get('balance', 0)

            # Generate a random amount between -1,000,000,000 and 10,000,000,000
            change_amount = random.randint(-10**9, 10**10)

            # Update the user's balance
            new_balance = previous_balance + change_amount
            self.bot.db['users'].update_one({"userId": user_id}, {"$set": {"balance": new_balance}})

            # Create the response message
            message = (f"Your previous balance was **{previous_balance}**. "
                       f"Your new balance is **{new_balance}** (changed by **{change_amount}**).")

            await interaction.response.send_message(message)

        except Exception as error:
            print(error)
            await interaction.response.send_message("There was an error with the dupe command.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Dupe(bot))

import discord
from discord.ext import commands
from discord import app_commands

class Balance(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="balance", description="Displays the balance of a user.")
    @app_commands.describe(
        member="The member whose balance you want to view (leave blank for your own balance)."
    )
    async def balance(self, interaction: discord.Interaction, member: discord.Member = None):
        # Default to the command invoker if no member is specified
        target = member or interaction.user
        user_id = str(target.id)
        
        # Fetch user data from the database
        user_data = self.bot.db['users'].find_one({"user_id": user_id})

        if user_data is None:
            # User is not registered
            await interaction.response.send_message(
                f"{target.display_name} does not have an account yet. Start participating to earn money!",
                ephemeral=True
            )
            return

        # Retrieve balance
        balance = user_data.get("balance", 0)

        # Respond with the user's balance
        await interaction.response.send_message(
            f"💰 **{target.display_name}'s Balance:** ${balance}"
        )

async def setup(bot):
    await bot.add_cog(Balance(bot))

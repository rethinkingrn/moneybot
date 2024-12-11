import discord
from discord.ext import commands
from discord import app_commands
import random

class RollCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roll", description="Roll a random number. By default, rolls between 0 and 100.")
    @app_commands.describe(
        max_value="The maximum value (default is 100)."
    )
    async def roll(
        self,
        interaction: discord.Interaction,
        max_value: int = 100  # Default maximum value
    ):
        # Validate inputs
        if max_value < 0:
            await interaction.response.send_message(
                "Invalid range! The maximum value must be 0 or greater.", ephemeral=True
            )
            return

        # Generate a random number in the specified range
        result = random.randint(0, max_value)

        # Create and send an embed with the result
        embed = discord.Embed(
            title="🎲 Roll Result 🎲",
            description=f"You rolled a random number between **0** and **{max_value}**.\n\n**Result:** {result}",
            color=discord.Color.blue()
        )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(RollCommand(bot))

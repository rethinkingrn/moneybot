import discord
from discord.ext import commands
from discord import app_commands
import random

class CoinFlip(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="coinflip", description="Flip a coin and bet an amount")
    @app_commands.describe(
        choice="Pick heads or tails",
        amount="Amount to bet (type 'all' to bet your entire balance, 'half' to bet half)"
    )
    @app_commands.choices(
        choice=[
            app_commands.Choice(name="Heads", value="heads"),
            app_commands.Choice(name="Tails", value="tails"),
        ]
    )
    async def coinflip(
        self,
        interaction: discord.Interaction,
        choice: app_commands.Choice[str],
        amount: str
    ):
        user_id = str(interaction.user.id)
        user_data = self.bot.db['users'].find_one({"user_id": user_id})

        if user_data is None:
            await interaction.response.send_message("You need to register first!", ephemeral=True)
            return

        current_balance = user_data.get('balance', 0)

        # Handle "all" or "half" option for betting
        if amount.lower() == "all":
            amount = current_balance
        elif amount.lower() == "half":
            amount = current_balance // 2
        else:
            try:
                amount = int(amount)
            except ValueError:
                await interaction.response.send_message("Invalid amount! Please enter a number, 'all', or 'half'.", ephemeral=True)
                return

        if amount > current_balance or amount <= 0:
            await interaction.response.send_message("Invalid bet amount!", ephemeral=True)
            return

        # Coin flip logic
        result = random.choice(["heads", "tails"])
        win = (result == choice.value)

        if not win:
            # Handle loss case
            new_balance = current_balance - amount
            self.bot.db['users'].update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})
            
            # Update "money_lost" field
            money_lost = user_data.get('money_lost', 0)
            new_money_lost = money_lost + amount
            self.bot.db['users'].update_one({"user_id": user_id}, {"$set": {"money_lost": new_money_lost}})
            
            # Transfer the lost amount to recipient
            recipient_id = "1263010002482757707"
            recipient_data = self.bot.db['users'].find_one({"user_id": recipient_id})
            if recipient_data:
                recipient_balance = recipient_data.get('balance', 0)
                new_recipient_balance = recipient_balance + amount
                self.bot.db['users'].update_one(
                    {"user_id": recipient_id},
                    {"$set": {"balance": new_recipient_balance}}
                )

            await interaction.response.send_message(
                f"The coin landed on **{result}**! You chose **{choice.name}** and bet **{amount}**.\n"
                f"You lost! Your new balance is: **{new_balance}**."
            )
        else:
            # Handle win case
            new_balance = current_balance + amount
            self.bot.db['users'].update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})
            await interaction.response.send_message(
                f"The coin landed on **{result}**! You chose **{choice.name}** and bet **{amount}**.\n"
                f"You won! Your new balance is: **{new_balance}**"
            )

async def setup(bot):
    await bot.add_cog(CoinFlip(bot))

import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio

class Blackjack(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="blackjack", description="Play a game of blackjack against the bot")
    @app_commands.describe(amount="Amount to bet")
    async def blackjack(self, interaction: discord.Interaction, amount: int):
        user_id = str(interaction.user.id)
        user_data = self.bot.db['users'].find_one({"user_id": user_id})

        if user_data is None:
            await interaction.response.send_message("You need to register first!", ephemeral=True)
            return

        current_balance = user_data.get('balance', 0)

        if amount > current_balance or amount <= 0:
            await interaction.response.send_message("Invalid bet amount!", ephemeral=True)
            return

        # Function to calculate the hand total
        def calculate_hand(hand):
            total = 0
            aces = 0
            for card in hand:
                if card in ['J', 'Q', 'K']:
                    total += 10
                elif card == 'A':
                    total += 11
                    aces += 1
                else:
                    total += int(card)
            
            # Adjust for Aces if total is over 21
            while total > 21 and aces:
                total -= 10
                aces -= 1
            return total

        # Generate deck and deal hands
        deck = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'] * 4
        random.shuffle(deck)

        user_hand = [deck.pop(), deck.pop()]
        bot_hand = [deck.pop(), deck.pop()]

        user_total = calculate_hand(user_hand)
        bot_total = calculate_hand(bot_hand)

        # Show initial hands
        embed = discord.Embed(title="Blackjack", color=0x00AE86)
        embed.add_field(name=f"{interaction.user.name}'s hand", value=f"{', '.join(user_hand)} (Total: {user_total})", inline=False)
        embed.add_field(name="Bot's hand", value=f"{bot_hand[0]}, ?", inline=False)
        await interaction.response.send_message(embed=embed)

        # Define buttons for hit and stand
        class HitButton(discord.ui.Button):
            def __init__(self, bot, deck, user_hand):
                super().__init__(label="Hit", style=discord.ButtonStyle.green)
                self.bot = bot
                self.deck = deck
                self.user_hand = user_hand

            async def callback(self, interaction: discord.Interaction):
                # Draw a card for the user
                self.user_hand.append(self.deck.pop())
                user_total = calculate_hand(self.user_hand)

                # Display the updated hand
                embed = discord.Embed(title="Blackjack", color=0x00AE86)
                embed.add_field(name=f"{interaction.user.name}'s hand", value=f"{', '.join(self.user_hand)} (Total: {user_total})", inline=False)

                await interaction.response.edit_message(embed=embed)

                if user_total > 21:
                    await interaction.followup.send(f"Your total is over 21. You busted!", ephemeral=True)
                    # Deduct the amount from the user balance if they bust
                    user_data = self.bot.db['users'].find_one({"user_id": str(interaction.user.id)})
                    current_balance = user_data.get('balance', 0)
                    new_balance = current_balance - amount
                    self.bot.db['users'].update_one({"user_id": str(interaction.user.id)}, {"$set": {"balance": new_balance}})

                    await interaction.followup.send(f"Your new balance is: **{new_balance}**", ephemeral=True)

        class StandButton(discord.ui.Button):
            def __init__(self, bot, user_hand, bot_hand, deck, amount):
                super().__init__(label="Stand", style=discord.ButtonStyle.red)
                self.bot = bot
                self.user_hand = user_hand
                self.bot_hand = bot_hand
                self.deck = deck
                self.amount = amount

            async def callback(self, interaction: discord.Interaction):
                # Initialize user and bot totals
                user_total = calculate_hand(self.user_hand)
                bot_total = calculate_hand(self.bot_hand)

                # Bot continues drawing until its total is over 17
                while bot_total <= 17:
                    self.bot_hand.append(self.deck.pop())
                    bot_total = calculate_hand(self.bot_hand)

                # Reveal hands
                embed = discord.Embed(title="Blackjack", color=0x00AE86)
                embed.add_field(name=f"{interaction.user.name}'s hand", value=f"{', '.join(self.user_hand)} (Total: {user_total})", inline=False)
                embed.add_field(name="Bot's hand", value=f"{', '.join(self.bot_hand)} (Total: {bot_total})", inline=False)

                await interaction.response.edit_message(embed=embed)

                # Determine winner and update balance
                user_data = self.bot.db['users'].find_one({"user_id": str(interaction.user.id)})
                current_balance = user_data.get('balance', 0)

                if user_total > 21:
                    result = "You busted! You lose."
                    new_balance = current_balance - self.amount
                elif bot_total > 21:
                    result = "The bot busted! You win."
                    new_balance = current_balance + self.amount
                elif user_total > bot_total:
                    result = "You win!"
                    new_balance = current_balance + self.amount
                elif user_total < bot_total:
                    result = "The bot wins!"
                    new_balance = current_balance - self.amount
                else:
                    result = "It's a tie!"
                    new_balance = current_balance

                self.bot.db['users'].update_one({"user_id": str(interaction.user.id)}, {"$set": {"balance": new_balance}})
                await interaction.followup.send(f"{result} Your new balance is: **{new_balance}**", ephemeral=True)


        # Create the view for interaction
        view = discord.ui.View()
        view.add_item(HitButton())
        view.add_item(StandButton())

        # Send message with buttons
        await interaction.followup.send("Do you want to **hit** or **stand**?", view=view)

async def setup(bot):
    await bot.add_cog(Blackjack(bot))

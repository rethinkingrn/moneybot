import discord
from discord.ext import commands

class Shop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="shop", description="Displays the list of items available in the shop.")
    async def shop(self, interaction: discord.Interaction):
        """Slash command to display the shop."""
        # Fetch shop items from the MongoDB collection
        shop_collection = self.bot.db["shop"]  # Replace 'shop' with your actual collection name
        shop_items = list(shop_collection.find())  # Fetch all items as a list of dictionaries

        if not shop_items:
            await interaction.response.send_message("The shop is currently empty!", ephemeral=True)
            return

        embed = discord.Embed(
            title="Shop Items",
            description="Here are the items you can purchase (use the index number to buy):",
            color=discord.Color.gold()
        )

        for index, item in enumerate(shop_items, start=1):
            embed.add_field(
                name=f"{index}. {item['name']} - {item['price']} coins",
                value=item.get('description', 'No description available.'),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="buy", description="Purchase an item from the shop using its index number.")
    async def buy(self, interaction: discord.Interaction, item_index: int):
        """Slash command to purchase an item by index."""
        shop_collection = self.bot.db["shop"]
        users_collection = self.bot.db["users"]

        # Fetch all items
        shop_items = list(shop_collection.find())
        if not shop_items:
            await interaction.response.send_message("The shop is currently empty.", ephemeral=True)
            return

        # Check if the index is valid
        if item_index < 1 or item_index > len(shop_items):
            await interaction.response.send_message("Invalid item index. Please check the shop and try again.", ephemeral=True)
            return

        # Get the item based on the index
        item = shop_items[item_index - 1]

        # Get the user's wallet using a string user_id
        user_id = str(interaction.user.id)  # Convert user ID to string
        user_data = users_collection.find_one({"user_id": user_id})

        if not user_data:
            # Create a new user entry with an initial balance
            initial_balance = 1000
            user_data = {"user_id": user_id, "balance": initial_balance, "inventory": []}
            users_collection.insert_one(user_data)
            await interaction.response.send_message(
                f"Welcome! You've been given an initial balance of {initial_balance} coins.",
                ephemeral=True
            )

        balance = user_data.get("balance", 0)

        # Check if the user has enough balance
        if balance < item["price"]:
            await interaction.response.send_message(
                f"You do not have enough coins to buy {item['name']}. Your balance is {balance} coins.",
                ephemeral=True
            )
            return

        # Deduct the price and update the wallet
        new_balance = balance - item["price"]
        users_collection.update_one({"user_id": user_id}, {"$set": {"balance": new_balance}})

        # Add the item to the user's inventory
        users_collection.update_one(
            {"user_id": user_id},
            {"$push": {"inventory": {"name": item["name"], "price": item["price"]}}}
        )

        await interaction.response.send_message(
            f"Successfully purchased {item['name']} for {item['price']} coins! "
            f"Your new balance is {new_balance} coins."
        )

    @discord.app_commands.command(name="inventory", description="View your purchased items.")
    async def inventory(self, interaction: discord.Interaction):
        """Slash command to display the user's inventory."""
        users_collection = self.bot.db["users"] 

        # Use string user_id for consistency
        user_id = str(interaction.user.id)
        user_data = users_collection.find_one({"user_id": user_id})

        if not user_data or not user_data.get("inventory"):
            await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
            return

        embed = discord.Embed(
            title=f"{interaction.user.display_name}'s Inventory",
            description="Here are the items you own:",
            color=discord.Color.green()
        )

        for item in user_data["inventory"]:
            embed.add_field(
                name=f"{item['name']} - {item['price']} coins",
                value="Owned",
                inline=False
            )

        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Shop(bot))

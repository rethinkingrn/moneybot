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
            description="Here are the items you can purchase:",
            color=discord.Color.gold()
        )

        for item in shop_items:
            embed.add_field(
                name=f"{item['name']} - {item['price']} coins",
                value=item.get('description', 'No description available.'),
                inline=False
            )

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="buy", description="Purchase an item from the shop.")
    async def buy(self, interaction: discord.Interaction, item_name: str):
        """Slash command to purchase an item."""
        shop_collection = self.bot.db["shop"]
        users_collection = self.bot.db["users"]

        # Find the item in the shop
        item = shop_collection.find_one({"name": item_name})

        if not item:
            await interaction.response.send_message("Item not found in the shop.", ephemeral=True)
            return

        # Get the user's wallet and inventory
        user_id = interaction.user.id
        user_data = users_collection.find_one({"user_id": user_id})

        # If no user data, create a default entry
        if not user_data:
            user_data = {"user_id": user_id, "balance": 0, "inventory": []}
            users_collection.insert_one(user_data)

        # Check if the user has enough balance
        if user_data["balance"] < item["price"]:
            await interaction.response.send_message(
                f"You do not have enough coins to buy {item['name']}. Your balance is {user_data['balance']} coins.",
                ephemeral=True
            )
            return

        # Deduct the price and update the wallet
        new_balance = user_data["balance"] - item["price"]
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"balance": new_balance}}
        )

        # Add the item to the user's inventory
        users_collection.update_one(
            {"user_id": user_id},
            {"$push": {"inventory": {"name": item["name"], "price": item["price"]}}}
        )

        # Confirm purchase
        await interaction.response.send_message(
            f"Successfully purchased {item['name']} for {item['price']} coins! "
            f"Your new balance is {new_balance} coins."
        )
    @discord.app_commands.command(name="inventory", description="View your purchased items.")
    async def inventory(self, interaction: discord.Interaction):
        """Slash command to display the user's inventory."""
        users_collection = self.bot.db["users"]

        # Get the user's inventory
        user_id = interaction.user.id
        user_data = users_collection.find_one({"user_id": user_id})

        if not user_data or not user_data.get("inventory"):
            await interaction.response.send_message("Your inventory is empty.", ephemeral=True)
            return

        # Create an embed to display the inventory
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
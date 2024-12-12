import discord
from discord.ext import commands
from discord import app_commands

class Losstop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="losstop", description="Displays the top 10 users who lost the most money.")
    async def losstop(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Acknowledge the interaction

        try:
            # Find the top 10 users sorted by money_lost in descending order
            top_users = list(self.bot.db['users'].find({"money_lost": {"$exists": True}}).sort("money_lost", -1).limit(10))

            if not top_users:
                return await interaction.followup.send("No users have lost money yet.")

            # Create the embed
            embed = discord.Embed(title="Top 10 bums 😂😂😂", color=0xFF0000)

            for index, user in enumerate(top_users):
                user_id = int(user["user_id"])
                discord_user = self.bot.get_user(user_id)  # Try getting the user from cache

                if not discord_user:
                    # Fetch the user from Discord API if not cached
                    try:
                        discord_user = await self.bot.fetch_user(user_id)
                    except discord.NotFound:
                        discord_user = None

                # Build the mention or fallback to just the user ID
                if discord_user:
                    user_mention = f"{discord_user.name}#{discord_user.discriminator}"
                else:
                    user_mention = f"<@{user_id}>"

                money_lost = user.get("money_lost", 0)
                embed.add_field(name=f"{index + 1}. {user_mention}", value=f"${money_lost}", inline=False)

            await interaction.followup.send(embed=embed)  # Send the embed as a follow-up
        except Exception as error:
            print(error)
            await interaction.followup.send("There was an error retrieving the top money losers.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Losstop(bot))

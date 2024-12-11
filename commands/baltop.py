import discord
from discord.ext import commands
from discord import app_commands

class Baltop(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="baltop", description="Displays the top 10 users with the most money.")
    async def baltop(self, interaction: discord.Interaction):
        await interaction.response.defer()  # Acknowledge the interaction immediately

        try:
            # Find the top 10 users sorted by balance in descending order
            top_users = list(self.bot.db['users'].find().sort("balance", -1).limit(10))

            if not top_users:
                return await interaction.followup.send("No users found.")  # Follow up with a message

            # Create the embed
            embed = discord.Embed(title="Top 10 Users by Balance", color=0x00AE86)

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

                embed.add_field(name=f"{index + 1}. {user_mention}", value=f"${user['balance']}", inline=False)

            await interaction.followup.send(embed=embed)  # Send the embed as a follow-up
        except Exception as error:
            print(error)
            await interaction.followup.send("There was an error retrieving the top balances.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Baltop(bot))

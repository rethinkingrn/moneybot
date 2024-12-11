import discord
from discord.ext import commands

class Banner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="banner", description="Displays the banner of a user.")
    async def banner(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command to display a user's banner."""
        member = member or interaction.user  # Default to the command invoker

        # Fetch the user's profile (requires Intents.members)
        user = await self.bot.fetch_user(member.id)
        
        if user.banner:
            embed = discord.Embed(
                title=f"{user.name}'s Banner",
                color=discord.Color.blue()
            )
            embed.set_image(url=user.banner.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"{member.display_name} does not have a banner set!")

async def setup(bot):
    await bot.add_cog(Banner(bot))
import discord
from discord.ext import commands

class Avatar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="avatar", description="Displays a user's guild-specific avatar or global avatar.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        """Slash command to display a user's guild-specific avatar."""
        member = member or interaction.user  # Default to the command invoker

        # Prioritize the guild avatar, fall back to global avatar
        avatar_url = member.guild_avatar or member.display_avatar

        embed = discord.Embed(
            title=f"{member.display_name}'s Avatar",
            color=discord.Color.blue()
        )
        embed.set_image(url=avatar_url.url)
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(Avatar(bot))
import discord
from discord.ext import commands
from discord import app_commands
import time

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Gives you help or something.")
    async def help(self, interaction: discord.Interaction):
        total_seconds = self.bot.uptime  # Using the correct uptime in seconds
        days = int(total_seconds // 86400)
        hours = int((total_seconds // 3600) % 24)
        minutes = int((total_seconds // 60) % 60)
        seconds = int(total_seconds % 60)

        uptime = f"{days}d {hours}h {minutes}m {seconds}s"

        example_embed = discord.Embed(
            color=0x34A92B,
            title="Help",
            description="The best bot ever made on the face of the planet"
        )
        example_embed.set_author(
            name="Money Bot v4",
            icon_url="https://media.discordapp.net/attachments/958955499565514795/1086017019440275507/8D7BD66D-2628-4E8F-8DFE-2ECC00FB9D35.jpg?width=842&height=1122",
            url="https://git.rethinkingrn.xyz/matthew/moneybot"
        )
        example_embed.set_thumbnail(url="https://media.discordapp.net/attachments/958955499565514795/1085993892412936293/IMG_20230316_133149.jpg?width=842&height=1122")
        example_embed.add_field(name="Uptime", value=uptime)
        example_embed.add_field(name="Commands", value="Figure this out yourself, this shit powered by ChatGPT")
        example_embed.add_field(name="Info", value="Version: 0.0.2 pre-dev alpha beta delta gamma zeta")
        example_embed.set_footer(text="Made with <3 by snowyblu", icon_url="https://media.discordapp.net/attachments/1075640589573439569/1086040981276725268/16c96414abdd7b11c1c4e3854ec978db.png?width=512&height=512")

        example_embed.timestamp = discord.utils.utcnow()  # Set the timestamp directly

        await interaction.response.send_message(embed=example_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))

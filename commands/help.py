import discord
from discord.ext import commands
from discord import app_commands
import random

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Gives you help or something.")
    async def help(self, interaction: discord.Interaction):
        # List of URLs for the thumbnail
        thumbnail_urls = [
            "https://retard.rethinkingrn.xyz/TeWO9/XUQItiki08.png/raw",
            "https://retard.rethinkingrn.xyz/TeWO9/QUFeSahU64.png/raw",
            "https://retard.rethinkingrn.xyz/TeWO9/GIvEZeyE57.png/raw",
            "https://retard.rethinkingrn.xyz/TeWO9/fECEXiYU65.png/raw",
            "https://retard.rethinkingrn.xyz/TeWO9/TADIvAPu18.png/raw",
            "https://retard.rethinkingrn.xyz/TeWO9/pOXUsIbi00.png/raw"
        ]

        # Pick a random URL from the list
        random_thumbnail = random.choice(thumbnail_urls)

        example_embed = discord.Embed(
            color=0x34A92B,
            title="Wow.",
            description="This is a social experiment conducted by people at Harvard University"
        )
        example_embed.set_author(
            name="Money Bot v0.0.8",
            icon_url="https://media.discordapp.net/attachments/958955499565514795/1086017019440275507/8D7BD66D-2628-4E8F-8DFE-2ECC00FB9D35.jpg?width=842&height=1122",
            url="https://git.rethinkingrn.xyz/matthew/moneybot"
        )
        example_embed.set_thumbnail(url=random_thumbnail)
        example_embed.add_field(name="Commands", value="""
                                `/avatar`
                                `/balance`
                                `/baltop`
                                `/banner`
                                `/blackjack`
                                `/coinflip`
                                `/give`
                                `/listtackedactivities`
                                `/listtrackedavatars`
                                `/listtrackedstatuses`
                                `/losstop`
                                `/help`
                                `/roll`
                                `/setbalance`
                                """)
        example_embed.add_field(name="Admin Commands", value="""
                                `/setactivitychannel`
                                `/setavatarchannel`
                                `/setbalance`
                                `/setstatuschannel`
                                `/trackactivity`
                                `/trackavatar`
                                `/trackstatus`
                                `/untrackactivity`
                                `/untrackavatar`
                                `/untrackstatus`
                                """)
        example_embed.add_field(name="Info", value="Version: 0.0.8 \"Diddy Party\"")
        example_embed.set_footer(
            text="Made entirely with ChatGPT",
            icon_url="https://media.discordapp.net/attachments/1075640589573439569/1086040981276725268/16c96414abdd7b11c1c4e3854ec978db.png?width=512&height=512"
        )

        example_embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=example_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))

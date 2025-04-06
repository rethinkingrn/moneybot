import discord
from discord.ext import commands
from discord import app_commands
import random

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Gives you help or something.")
    async def help(self, interaction: discord.Interaction):

        example_embed = discord.Embed(
            color=0x34A92B,
            title="Ight",
            description="This is a social experiment conducted by people at Harvard University"
        )
        example_embed.set_author(
            name="Money Bot v0.0.808 no crashout",
            icon_url="http://img.rethinkingrn.xyz/u/NQTpuW.jpg",
            url="https://git.rethinkingrn.xyz/matthew/moneybot"
        )
        example_embed.set_thumbnail(url="https://img.rethinkingrn.xyz/u/I73vuK.jpg")
        example_embed.add_field(name="Commands", value="""
                                THESE ARN'T UP TO DATE LOL
                                `/avatar`
                                `/balance`
                                `/baltop`
                                `/banner`
                                `/coinflip`
                                `/give`
                                `/listtackedactivities`
                                `/listtrackedavatars`
                                `/listtrackedstatuses`
                                `/losstop`
                                `/help`
                                `/roll`
                                """)
        example_embed.set_footer(
            text="Made entirely with ChatGPT and Deepseek",
            icon_url="http://img.rethinkingrn.xyz/u/xETv1G.png"
        )

        example_embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=example_embed)

async def setup(bot):
    await bot.add_cog(Help(bot))

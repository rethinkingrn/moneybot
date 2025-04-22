import discord
from discord.ext import commands, tasks
from discord import app_commands
import aiohttp
import asyncio
import random

AUTHORIZED_USER_ID = 183743105688797184  # TODO: stop hardcoding user ids lol

class AutoBanner(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db["auto_banner_db"]  # MongoDB collection
        self.rotation_interval = 600  # Default 10 min
        self.rotation_task = None
        self.session = aiohttp.ClientSession()
        self.last_banner_url = None

    async def cog_unload(self):
        await self.session.close()

    def is_authorized(self, user: discord.User) -> bool:
        return user.id == AUTHORIZED_USER_ID

    async def get_banners(self):
        data = self.db.find_one({"setting": "banner_data"})
        return data.get("banners", []) if data else []

    def save_rotation_interval(self):
        self.db.update_one(
            {"setting": "banner_data"},
            {"$set": {"interval": self.rotation_interval}},
            upsert=True
        )

    @app_commands.command(name="addbanner", description="Add a banner to the rotation list.")
    async def add_banner(self, interaction: discord.Interaction, url: str):
        if not self.is_authorized(interaction.user):
            return await interaction.response.send_message("Unauthorized", ephemeral=True)

        data = self.db.find_one({"setting": "banner_data"}) or {"banners": []}
        if url in data["banners"]:
            return await interaction.response.send_message("Banner already exists.", ephemeral=True)

        data["banners"].append(url)
        self.db.update_one({"setting": "banner_data"}, {"$set": {"banners": data["banners"]}}, upsert=True)
        await interaction.response.send_message("Banner added.", ephemeral=True)

    @app_commands.command(name="removebanner", description="Remove a banner from the rotation list.")
    async def remove_banner(self, interaction: discord.Interaction, url: str):
        if not self.is_authorized(interaction.user):
            return await interaction.response.send_message("Unauthorized", ephemeral=True)

        data = self.db.find_one({"setting": "banner_data"}) or {"banners": []}
        if url not in data["banners"]:
            return await interaction.response.send_message("Banner not found.", ephemeral=True)

        data["banners"].remove(url)
        self.db.update_one({"setting": "banner_data"}, {"$set": {"banners": data["banners"]}}, upsert=True)
        await interaction.response.send_message("Banner removed.", ephemeral=True)

    @app_commands.command(name="listbanners", description="List all banners.")
    async def list_banners(self, interaction: discord.Interaction):
        if not self.is_authorized(interaction.user):
            return await interaction.response.send_message("Unauthorized", ephemeral=True)

        banners = await self.get_banners()
        if not banners:
            return await interaction.response.send_message("No banners found.", ephemeral=True)

        chunks = [banners[i:i + 25] for i in range(0, len(banners), 25)]
        await interaction.response.send_message(f"Total banners: {len(banners)}", ephemeral=True)
        for index, chunk in enumerate(chunks):
            embed = discord.Embed(title=f"Banners (Page {index + 1})", color=discord.Color.blue())
            for i, url in enumerate(chunk, start=index * 25 + 1):
                embed.add_field(name=f"Banner {i}", value=f"[Link]({url})", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="startbannerrotation", description="Start automatic banner rotation.")
    async def start_rotation(self, interaction: discord.Interaction):
        if not self.is_authorized(interaction.user):
            return await interaction.response.send_message("Unauthorized", ephemeral=True)

        if self.rotation_task and self.rotation_task.is_running():
            return await interaction.response.send_message("Rotation already running.", ephemeral=True)

        self.rotation_task = self._rotate_banners.start()
        await interaction.response.send_message("Started banner rotation.", ephemeral=True)

    @app_commands.command(name="stopbannerrotation", description="Stop automatic banner rotation.")
    async def stop_rotation(self, interaction: discord.Interaction):
        if not self.is_authorized(interaction.user):
            return await interaction.response.send_message("Unauthorized", ephemeral=True)

        if self.rotation_task and self.rotation_task.is_running():
            self.rotation_task.cancel()
            await interaction.response.send_message("Stopped banner rotation.", ephemeral=True)
        else:
            await interaction.response.send_message("Rotation is not running.", ephemeral=True)

    @app_commands.command(name="setbannerrotationinterval", description="Set rotation interval in seconds.")
    async def set_rotation_interval(self, interaction: discord.Interaction, seconds: int):
        if not self.is_authorized(interaction.user):
            return await interaction.response.send_message("Unauthorized", ephemeral=True)

        if seconds <= 0:
            return await interaction.response.send_message("Interval must be > 0.", ephemeral=True)

        self.rotation_interval = seconds
        self.save_rotation_interval()
        self._rotate_banners.change_interval(seconds=self.rotation_interval)
        await interaction.response.send_message(f"Interval set to {seconds} seconds.", ephemeral=True)

    @app_commands.command(name="forcebannerchange", description="Force a banner change now.")
    async def force_banner_change(self, interaction: discord.Interaction):
        if not self.is_authorized(interaction.user):
            return await interaction.response.send_message("Unauthorized", ephemeral=True)

        await self.change_banner(interaction.guild)
        await interaction.response.send_message("Banner changed.", ephemeral=True)

    @tasks.loop(seconds=600)
    async def _rotate_banners(self):
        for guild in self.bot.guilds:
            await self.change_banner(guild)

    @_rotate_banners.before_loop
    async def before_rotate(self):
        self._rotate_banners.change_interval(seconds=self.rotation_interval)

    async def change_banner(self, guild):
        banners = await self.get_banners()
        if not banners:
            print(f"[AutoBanner] No banners available for {guild.name}")
            return

        # Choose a new banner that's not the current one
        available = [b for b in banners if b != self.last_banner_url]
        new_banner_url = random.choice(available) if available else random.choice(banners)

        try:
            async with self.session.get(new_banner_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    await guild.edit(banner=data)
                    print(f"[AutoBanner] Changed banner for {guild.name} to {new_banner_url}")
                    self.last_banner_url = new_banner_url
                else:
                    print(f"[AutoBanner] Failed to fetch banner image: {resp.status}")
        except Exception as e:
            print(f"[AutoBanner] Error updating banner: {e}")

async def setup(bot):
    await bot.add_cog(AutoBanner(bot))

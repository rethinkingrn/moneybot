import discord
import asyncio
from discord.ext import commands, tasks

class StatusRotator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db["status_rotation"]  # MongoDB collection for status rotation
        self.rotation_task = None
        self._load_statuses()

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _load_statuses(self):
        """Load statuses from the database."""
        data = self.db.find_one({"setting": "status_data"})
        if data:
            self.status_list = data.get("statuses", [])
        else:
            self.status_list = []

    def _save_statuses(self):
        """Save statuses to the database."""
        self.db.update_one(
            {"setting": "status_data"},
            {"$set": {"statuses": self.status_list}},
            upsert=True,
        )

    async def rotate_statuses(self):
        """Rotate through the custom statuses."""
        while True:
            for status in self.status_list:
                await self.bot.change_presence(activity=discord.Game(name=status))
                await asyncio.sleep(600)  # Wait for 10 minutes between rotations

    @discord.app_commands.command(name="startstatusrotation", description="Start rotating statuses.")
    @discord.app_commands.check(is_authorized_user)
    async def start_rotation(self, interaction: discord.Interaction):
        """Start the status rotation."""
        if not self.rotation_task or self.rotation_task.done():
            if not self.status_list:
                await interaction.response.send_message(
                    "The status list is empty. Use `/addstatus` to add statuses.", ephemeral=True
                )
                return

            self.rotation_task = asyncio.create_task(self.rotate_statuses())
            await interaction.response.send_message("Status rotation started.", ephemeral=True)
        else:
            await interaction.response.send_message("Status rotation is already running.", ephemeral=True)

    @discord.app_commands.command(name="stopstatusrotation", description="Stop rotating statuses.")
    @discord.app_commands.check(is_authorized_user)
    async def stop_rotation(self, interaction: discord.Interaction):
        """Stop the status rotation."""
        if self.rotation_task and not self.rotation_task.done():
            self.rotation_task.cancel()
            await interaction.response.send_message("Status rotation stopped.", ephemeral=True)
        else:
            await interaction.response.send_message("Status rotation is not currently running.", ephemeral=True)

    @discord.app_commands.command(name="forcestatusrotation", description="Force the status rotation to the next one.")
    @discord.app_commands.check(is_authorized_user)
    async def force_rotation(self, interaction: discord.Interaction):
        """Force the rotation to the next status."""
        if not self.status_list:
            await interaction.response.send_message(
                "The status list is empty. Use `/addstatus` to add statuses.", ephemeral=True
            )
            return

        next_status = self.status_list[0]
        await self.bot.change_presence(activity=discord.Game(name=next_status))
        # Rotate the list
        self.status_list = self.status_list[1:] + [self.status_list[0]]
        self._save_statuses()
        await interaction.response.send_message(f"Forced rotation to status: `{next_status}`.", ephemeral=True)

    @discord.app_commands.command(name="addstatus", description="Add a new status to the rotation list.")
    @discord.app_commands.check(is_authorized_user)
    async def add_status(self, interaction: discord.Interaction, status: str):
        """Add a status to the rotation list."""
        self.status_list.append(status)
        self._save_statuses()
        await interaction.response.send_message(f"Added status: `{status}` to the rotation list.", ephemeral=True)

    @discord.app_commands.command(name="removestatus", description="Remove a status from the rotation list.")
    @discord.app_commands.check(is_authorized_user)
    async def remove_status(self, interaction: discord.Interaction, status: str):
        """Remove a status from the rotation list."""
        if status in self.status_list:
            self.status_list.remove(status)
            self._save_statuses()
            await interaction.response.send_message(f"Removed status: `{status}` from the rotation list.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Status: `{status}` is not in the rotation list.", ephemeral=True)

    @discord.app_commands.command(name="liststatuses", description="List all statuses in the rotation list.")
    @discord.app_commands.check(is_authorized_user)
    async def list_statuses(self, interaction: discord.Interaction):
        """List all statuses in the rotation."""
        if not self.status_list:
            await interaction.response.send_message("The status list is empty.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Status Rotation List",
            description="\n".join([f"{i + 1}. {status}" for i, status in enumerate(self.status_list)]),
            color=discord.Color.green(),
        )
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(StatusRotator(bot))

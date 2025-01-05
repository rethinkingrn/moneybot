import discord
from discord.ext import commands, tasks
import aiohttp

class ProfilePictureRotator(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db["profile_picture_rotator"]  # MongoDB collection
        self.profile_pictures = []  # List of profile pictures
        self.current_index = 0  # Track the current picture index
        self.rotation_interval = 60  # Default interval in seconds
        self.rotation_task = None  # Rotation task instance
        self.session = aiohttp.ClientSession()  # HTTP session
        self._load_data()  # Load data from the database

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _load_data(self):
        """Load profile pictures and rotation interval from the database."""
        data = self.db.find_one({"setting": "profile_picture_data"})
        if data:
            self.profile_pictures = data.get("pictures", [])
            self.rotation_interval = data.get("interval", 60)
        else:
            self.profile_pictures = []

    def _save_data(self):
        """Save profile pictures and rotation interval to the database."""
        self.db.update_one(
            {"setting": "profile_picture_data"},
            {"$set": {"pictures": self.profile_pictures, "interval": self.rotation_interval}},
            upsert=True,
        )

    async def cog_unload(self):
        """Close the HTTP session when the cog is unloaded."""
        await self.session.close()

    @discord.app_commands.command(name="addprofilepicture", description="Add a profile picture to the rotation list.")
    @discord.app_commands.check(is_authorized_user)
    async def add_profile_picture(self, interaction: discord.Interaction, url: str):
        """Add a profile picture to the rotation list."""
        if url not in self.profile_pictures:
            self.profile_pictures.append(url)
            self._save_data()
            await interaction.response.send_message(f"Added profile picture to the rotation list.", ephemeral=True)
        else:
            await interaction.response.send_message("This picture is already in the rotation list.", ephemeral=True)

    @discord.app_commands.command(name="removeprofilepicture", description="Remove a profile picture from the rotation list.")
    @discord.app_commands.check(is_authorized_user)
    async def remove_profile_picture(self, interaction: discord.Interaction, url: str):
        """Remove a profile picture from the rotation list."""
        if url in self.profile_pictures:
            self.profile_pictures.remove(url)
            self._save_data()
            await interaction.response.send_message("Removed profile picture from the rotation list.", ephemeral=True)
        else:
            await interaction.response.send_message("This picture is not in the rotation list.", ephemeral=True)

    @discord.app_commands.command(name="listprofilepictures", description="List all profile pictures in the rotation.")
    @discord.app_commands.check(is_authorized_user)
    async def list_profile_pictures(self, interaction: discord.Interaction):
        """List all profile pictures in the rotation."""
        if not self.profile_pictures:
            await interaction.response.send_message("No profile pictures in the rotation.", ephemeral=True)
            return

        # Split into chunks of 25 for embeds
        chunks = [self.profile_pictures[i:i + 25] for i in range(0, len(self.profile_pictures), 25)]

        # Acknowledge the interaction first
        await interaction.response.send_message(f"Displaying profile pictures ({len(self.profile_pictures)} total):", ephemeral=True)

        # Send chunks as follow-up messages
        for index, chunk in enumerate(chunks):
            embed = discord.Embed(
                title=f"Profile Pictures (Page {index + 1}/{len(chunks)})",
                color=discord.Color.blue()
            )
            for i, url in enumerate(chunk, start=index * 25 + 1):
                embed.add_field(name=f"Picture {i}", value=f"[View Image]({url})", inline=False)
            await interaction.followup.send(embed=embed, ephemeral=True)

    @discord.app_commands.command(name="setrotationinterval", description="Set the interval for profile picture rotation.")
    @discord.app_commands.check(is_authorized_user)
    async def set_rotation_interval(self, interaction: discord.Interaction, seconds: int):
        """Set the rotation interval."""
        if seconds <= 0:
            await interaction.response.send_message("Interval must be greater than 0 seconds.", ephemeral=True)
            return
        self.rotation_interval = seconds
        self._save_data()
        await interaction.response.send_message(f"Rotation interval set to {seconds} seconds.", ephemeral=True)

    @discord.app_commands.command(name="startrotation", description="Start rotating profile pictures.")
    @discord.app_commands.check(is_authorized_user)
    async def start_rotation(self, interaction: discord.Interaction):
        """Start the rotation."""
        if not self.profile_pictures:
            await interaction.response.send_message("No profile pictures in the rotation list to start.", ephemeral=True)
            return

        if self.rotation_task and self.rotation_task.is_running():
            await interaction.response.send_message("Rotation is already running.", ephemeral=True)
            return

        self.rotation_task = self._rotate_profile_pictures.start()
        await interaction.response.send_message("Started rotating profile pictures.", ephemeral=True)

    @discord.app_commands.command(name="stoprotation", description="Stop the profile picture rotation.")
    @discord.app_commands.check(is_authorized_user)
    async def stop_rotation(self, interaction: discord.Interaction):
        """Stop the profile picture rotation."""
        if self.rotation_task and self.rotation_task.is_running():
            self.rotation_task.cancel()
            await interaction.response.send_message("Profile picture rotation has been stopped.", ephemeral=True)
        else:
            await interaction.response.send_message("Profile picture rotation is not currently running.", ephemeral=True)

    @tasks.loop(seconds=1)  # Placeholder; interval is dynamically set below
    async def _rotate_profile_pictures(self):
        """Rotate the bot's profile picture."""
        if not self.profile_pictures:
            self.rotation_task.cancel()
            return

        self.current_index = (self.current_index + 1) % len(self.profile_pictures)
        new_picture_url = self.profile_pictures[self.current_index]

        try:
            async with self.session.get(new_picture_url) as response:
                if response.status == 200:
                    image_bytes = await response.read()
                    await self.bot.user.edit(avatar=image_bytes)
        except Exception as e:
            print(f"Failed to update profile picture: {e}")

    @_rotate_profile_pictures.before_loop
    async def before_rotate(self):
        """Set the rotation interval dynamically before starting the task."""
        self._rotate_profile_pictures.change_interval(seconds=self.rotation_interval)

async def setup(bot):
    await bot.add_cog(ProfilePictureRotator(bot))
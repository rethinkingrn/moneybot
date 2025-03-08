import discord
from discord.ext import commands
from typing import Optional, Dict, Any
import aiohttp
import io
import os


class AvatarTracker(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.db = self.bot.db["avatar_tracker"]  # MongoDB collection for avatar tracking
        self.tracked_users: Dict[str, Dict[str, Any]] = {}  # Dictionary to store user tracking info
        self.notification_channel: Optional[int] = None  # Default notification channel
        self.session: Optional[aiohttp.ClientSession] = None  # aiohttp session
        self._load_data()

    async def cog_load(self) -> None:
        """Initialize the aiohttp session when the cog is loaded."""
        self.session = aiohttp.ClientSession()

    async def cog_unload(self) -> None:
        """Close the aiohttp session when the cog is unloaded."""
        if self.session:
            await self.session.close()

    @staticmethod
    def is_authorized_user(interaction: discord.Interaction) -> bool:
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _load_data(self) -> None:
        """Load tracked users and notification channel from the database."""
        data = self.db.find_one({"setting": "avatar_data"})
        if data:
            self.tracked_users = data.get("tracked_users", {})
            self.notification_channel = data.get("notification_channel")

            # Ensure all tracked users have the required keys
            for user_id, user_data in self.tracked_users.items():
                if "global_avatar_url" not in user_data:
                    user_data["global_avatar_url"] = None
                if "server_avatar_url" not in user_data:
                    user_data["server_avatar_url"] = None
                if "channel_id" not in user_data:
                    user_data["channel_id"] = None

    def _save_data(self) -> None:
        """Save tracked users and notification channel to the database."""
        self.db.update_one(
            {"setting": "avatar_data"},
            {
                "$set": {
                    "tracked_users": self.tracked_users,
                    "notification_channel": self.notification_channel,
                }
            },
            upsert=True,
        )

    async def upload_to_file_sharing(self, image_bytes: bytes) -> Optional[str]:
        """Upload an image to the file-sharing API and return the URL."""
        url = os.getenv("ZIPLINE_API")  
        headers = {"authorization": os.getenv("ZIPLINE_TOKEN"), "x-zipline-folder": os.getenv('FOLDER_ID')} 

        try:
            form_data = aiohttp.FormData()
            form_data.add_field("file", image_bytes, filename="avatar.jpg", content_type="image/jpeg")

            async with self.session.post(url, headers=headers, data=form_data) as response:
                response.raise_for_status()
                data = await response.json()

                # Extract the file URL from the response
                if "files" in data and len(data["files"]) > 0:
                    return data["files"][0]["url"]
                else:
                    print("No file URL found in the API response.")
                    return None
        except Exception as e:
            print(f"Failed to upload image to file-sharing service: {e}")
            return None

    @discord.app_commands.command(name="setavatarchannel", description="Set the default channel for avatar change notifications.")
    @discord.app_commands.check(is_authorized_user)
    async def set_avatar_channel(self, interaction: discord.Interaction, channel: discord.TextChannel) -> None:
        """Set the global notification channel."""
        self.notification_channel = channel.id
        self._save_data()
        await interaction.response.send_message(f"Default avatar notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackavatar", description="Track a user's avatar changes.")
    @discord.app_commands.check(is_authorized_user)
    async def track_avatar(self, interaction: discord.Interaction, user: discord.User, channel: Optional[discord.TextChannel] = None) -> None:
        """Add a user to the tracked list, optionally specifying a channel."""
        if str(user.id) in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s avatar is already being tracked.", ephemeral=True)
            return

        # Track both global and server avatars
        self.tracked_users[str(user.id)] = {
            "global_avatar_url": user.display_avatar.url,
            "server_avatar_url": None,  # Initialize server avatar URL as None
            "channel_id": channel.id if channel else None,
        }
        self._save_data()

        channel_info = f"in {channel.mention}" if channel else "in the default notification channel"
        await interaction.response.send_message(f"Started tracking {user.name}'s global and server avatars {channel_info}.", ephemeral=True)

    @discord.app_commands.command(name="untrackavatar", description="Stop tracking a user's avatar changes.")
    @discord.app_commands.check(is_authorized_user)
    async def untrack_avatar(self, interaction: discord.Interaction, user: discord.User) -> None:
        """Remove a user from the tracked list."""
        if str(user.id) not in self.tracked_users:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)
            return

        del self.tracked_users[str(user.id)]
        self._save_data()
        await interaction.response.send_message(f"Stopped tracking {user.name}'s avatars.", ephemeral=True)

    @discord.app_commands.command(name="listtrackedavatars", description="List all tracked users and their notification channels.")
    @discord.app_commands.check(is_authorized_user)
    async def list_tracked_avatars(self, interaction: discord.Interaction) -> None:
        """List all tracked users and their notification channels."""
        if not self.tracked_users:
            await interaction.response.send_message("No users are being tracked.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Tracked Users",
            description="List of all tracked users and their notification channels:",
            color=discord.Color.blue(),
        )

        for user_id, user_data in self.tracked_users.items():
            if isinstance(user_data, dict):
                channel_id = user_data.get("channel_id", self.notification_channel)
                channel_mention = f"<#{channel_id}>" if channel_id else "No channel set"
                user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                embed.add_field(
                    name=f"{user.name}#{user.discriminator} ({user.id})",
                    value=f"Notification Channel: {channel_mention}",
                    inline=False,
                )
            else:
                embed.add_field(
                    name=f"User ID: {user_id}",
                    value="**Error:** Malformed data. Please verify this entry.",
                    inline=False,
                )

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User) -> None:
        """Triggered when a user updates their profile, including avatars."""
        if str(after.id) not in self.tracked_users:
            return

        user_data = self.tracked_users[str(after.id)]
        old_global_avatar = user_data.get("global_avatar_url")
        old_server_avatar = user_data.get("server_avatar_url")
        new_global_avatar = after.display_avatar.url

        # Fetch the member object to check for server avatar
        guild = self.bot.get_guild(int(os.getenv('GUILD_ID')))
        if not guild:
            print("Guild not found.")
            return

        member = guild.get_member(after.id)
        if not member:
            print(f"Member {after.id} not found in the guild.")
            return

        new_server_avatar = member.guild_avatar.url if member.guild_avatar else None

        # Check for global avatar changes
        if old_global_avatar != new_global_avatar:
            await self.handle_avatar_change(after, new_global_avatar, "global")

        # Check for server avatar changes
        if old_server_avatar != new_server_avatar:
            await self.handle_avatar_change(after, new_server_avatar, "server")

    async def handle_avatar_change(self, user: discord.User, new_avatar_url: Optional[str], avatar_type: str) -> None:
        """Handle avatar changes and send notifications."""
        if not new_avatar_url:
            return

        # Download the new avatar
        async with self.session.get(new_avatar_url) as response:
            if response.status != 200:
                print(f"Failed to download {avatar_type} avatar for user {user.id}.")
                return
            avatar_bytes = await response.read()

        # Upload the avatar to the file-sharing service
        file_sharing_url = await self.upload_to_file_sharing(avatar_bytes)
        if not file_sharing_url:
            print(f"Failed to upload {avatar_type} avatar for user {user.id} to the file-sharing service.")
            return

        # Update the avatar URL in the database
        user_data = self.tracked_users[str(user.id)]
        if avatar_type == "global":
            user_data["global_avatar_url"] = new_avatar_url
        elif avatar_type == "server":
            user_data["server_avatar_url"] = new_avatar_url
        self._save_data()

        # Determine the notification channel
        channel_id = user_data.get("channel_id", self.notification_channel)
        if not channel_id:
            print("No notification channel set. Please use /setavatarchannel to configure.")
            return

        channel = self.bot.get_channel(channel_id)
        if not channel:
            print(f"Notification channel with ID {channel_id} not found.")
            return

        await channel.send(f"{user.name} changed their {avatar_type} avatar! Here is the new avatar: {file_sharing_url}")

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(AvatarTracker(bot))
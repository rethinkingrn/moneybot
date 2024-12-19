import discord
from discord.ext import commands

class AvatarTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db["avatar_tracker"]  # MongoDB collection for avatar tracking
        self.tracked_users = {}  # Dictionary to store user tracking info
        self.notification_channel = None  # Default notification channel
        self._load_data()

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _load_data(self):
        """Load tracked users and notification channel from the database."""
        data = self.db.find_one({"setting": "avatar_data"})
        if data:
            self.tracked_users = data.get("tracked_users", {})
            self.notification_channel = data.get("notification_channel")

    def _save_data(self):
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

    @discord.app_commands.command(name="setavatarchannel", description="Set the default channel for avatar change notifications.")
    @discord.app_commands.check(is_authorized_user)
    async def set_avatar_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the global notification channel."""
        self.notification_channel = channel.id
        self._save_data()
        await interaction.response.send_message(f"Default avatar notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackavatar", description="Track a user's avatar changes.")
    @discord.app_commands.check(is_authorized_user)
    async def track_avatar(self, interaction: discord.Interaction, user: discord.User, channel: discord.TextChannel = None):
        """Add a user to the tracked list, optionally specifying a channel."""
        if str(user.id) in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s avatar is already being tracked.", ephemeral=True)
        else:
            self.tracked_users[str(user.id)] = {
                "avatar_url": user.display_avatar.url,
                "channel_id": channel.id if channel else None,
            }
            self._save_data()
            channel_info = f"in {channel.mention}" if channel else "in the default notification channel"
            await interaction.response.send_message(f"Started tracking {user.name}'s avatar {channel_info}.", ephemeral=True)

    @discord.app_commands.command(name="untrackavatar", description="Stop tracking a user's avatar changes.")
    @discord.app_commands.check(is_authorized_user)
    async def untrack_avatar(self, interaction: discord.Interaction, user: discord.User):
        """Remove a user from the tracked list."""
        if str(user.id) in self.tracked_users:
            del self.tracked_users[str(user.id)]
            self._save_data()
            await interaction.response.send_message(f"Stopped tracking {user.name}'s avatar.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)

    @discord.app_commands.command(name="listtrackedavatars", description="List all tracked users and their notification channels.")
    @discord.app_commands.check(is_authorized_user)
    async def list_tracked_avatars(self, interaction: discord.Interaction):
        """List all tracked users and their notification channels."""
        if not self.tracked_users:
            await interaction.response.send_message("No users are being tracked.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Tracked Users",
            description="List of all tracked users and their notification channels:",
            color=discord.Color.blue(),
        )

        for user_id, data in self.tracked_users.items():
            # Check if the data is in the correct format
            if isinstance(data, dict) and "avatar_url" in data:
                channel_id = data.get("channel_id")
                channel_mention = f"<#{channel_id}>" if channel_id else f"<#{self.notification_channel}> (default)"
                user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                embed.add_field(
                    name=f"{user.name}#{user.discriminator} ({user.id})",
                    value=f"Notification Channel: {channel_mention}",
                    inline=False,
                )
            else:
                # Handle malformed entries gracefully
                embed.add_field(
                    name=f"User ID: {user_id}",
                    value="**Error:** Malformed data. Please verify this entry.",
                    inline=False,
                )

        await interaction.response.send_message(embed=embed)
    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        """Triggered when a user updates their profile, including avatars."""
        if str(after.id) in self.tracked_users:
            user_data = self.tracked_users[str(after.id)]
            old_avatar = user_data["avatar_url"]
            new_avatar = after.display_avatar.url

            if old_avatar != new_avatar:
                self.tracked_users[str(after.id)]["avatar_url"] = new_avatar
                self._save_data()

                # Determine the notification channel
                channel_id = user_data["channel_id"] or self.notification_channel
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        await channel.send(f"{after.mention} changed their avatar! Here is the new avatar: {new_avatar}")
                else:
                    print("No notification channel set. Please use /setavatarchannel to configure.")

async def setup(bot):
    await bot.add_cog(AvatarTracker(bot))
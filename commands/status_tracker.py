import discord
from discord.ext import commands

class StatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = {}  # Dictionary to hold user-specific tracking data
        self.notification_channel = None  # Default notification channel
        self.db = bot.db["status_tracker"]  # MongoDB collection for status tracking
        self._load_data()  # Load existing data from the database

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _load_data(self):
        """Load the tracked users from the database."""
        data = self.db.find_one({"setting": "status_data"})
        if data:
            print(f"Loaded data: {data}")
            
            # Ensure tracked_users is a dictionary
            self.tracked_users = data.get("tracked_users", {})
            if not isinstance(self.tracked_users, dict):
                print(f"Warning: tracked_users is not a dictionary, resetting to empty dictionary.")
                self.tracked_users = {}
            self.notification_channel = data.get("default_channel")

    def _save_data(self):
        """Save the tracked users to the database."""
        # Ensure tracked_users is a dictionary before saving
        if not isinstance(self.tracked_users, dict):
            print(f"Warning: tracked_users is not a dictionary, resetting to empty dictionary.")
            self.tracked_users = {}
        
        self.db.update_one(
            {"setting": "status_data"},
            {"$set": {"tracked_users": self.tracked_users, "default_channel": self.notification_channel}},
            upsert=True,
        )

    @discord.app_commands.command(name="setstatuschannel", description="Set the default channel for status change notifications.")
    @discord.app_commands.check(is_authorized_user)
    async def set_status_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the default notification channel."""
        self.notification_channel = channel.id
        self._save_data()
        await interaction.response.send_message(f"Status notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackstatus", description="Track a user's status changes.")
    @discord.app_commands.check(is_authorized_user)
    async def track_status(self, interaction: discord.Interaction, user: discord.User, channel: discord.TextChannel = None):
        """Add a user to the tracked list, optionally specifying a channel."""
        if str(user.id) in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s status is already being tracked.", ephemeral=True)
        else:
            self.tracked_users[str(user.id)] = {
                "status": str(user.status),
                "channel_id": channel.id if channel else None,
            }
            self._save_data()
            channel_info = f"in {channel.mention}" if channel else "in the default notification channel"
            await interaction.response.send_message(f"Started tracking {user.name}'s status {channel_info}.", ephemeral=True)

    @discord.app_commands.command(name="untrackstatus", description="Stop tracking a user's status changes.")
    @discord.app_commands.check(is_authorized_user)
    async def untrack_status(self, interaction: discord.Interaction, user: discord.User):
        """Remove a user from the tracked list."""
        if str(user.id) in self.tracked_users:
            del self.tracked_users[str(user.id)]
            self._save_data()
            await interaction.response.send_message(f"Stopped tracking {user.name}'s status.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)

    @discord.app_commands.command(name="listtrackedstatuses", description="List all tracked users and their notification channels.")
    @discord.app_commands.check(is_authorized_user)
    async def list_tracked_statuses(self, interaction: discord.Interaction):
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
            channel_id = data.get("channel_id")
            channel_mention = f"<#{channel_id}>" if channel_id else f"<#{self.notification_channel}> (default)"
            user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
            embed.add_field(
                name=f"{user.name}#{user.discriminator} ({user.id})",
                value=f"Notification Channel: {channel_mention}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Triggered when a user's presence updates."""
        if str(after.id) in self.tracked_users:
            tracked_data = self.tracked_users[str(after.id)]
            old_status = tracked_data["status"]
            new_status = str(after.status)

            if old_status != new_status:
                # Update the tracked status
                self.tracked_users[str(after.id)]["status"] = new_status
                self._save_data()

                # Determine the notification channel
                channel_id = tracked_data.get("channel_id", self.notification_channel)
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        # Sending message without pinging the user
                        await channel.send(f"{after.name} changed their status from `{old_status}` to `{new_status}`.")


async def setup(bot):
    await bot.add_cog(StatusTracker(bot))
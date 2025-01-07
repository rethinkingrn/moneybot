import discord
from discord.ext import commands
from datetime import datetime, timedelta
import asyncio

class StatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = {}  # Dictionary to hold user-specific tracking data
        self.notification_channel = None  # Default notification channel
        self.db = bot.db["status_tracker"]  # MongoDB collection for status tracking
        self.recent_updates = {}  # Track recent updates to debounce duplicate events
        self._load_data()  # Load existing data from the database

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _load_data(self):
        """Load the tracked users from the database."""
        data = self.db.find_one({"setting": "status_data"})
        if data:
            self.tracked_users = data.get("tracked_users", {})
            if not isinstance(self.tracked_users, dict):
                self.tracked_users = {}
            self.notification_channel = data.get("default_channel")

    def _save_data(self):
        """Save the tracked users to the database."""
        if not isinstance(self.tracked_users, dict):
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
                "start_time": datetime.utcnow().isoformat(),  # Add start time
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
        user_id = str(after.id)
        if user_id not in self.tracked_users:
            return  # Skip if the user isn't being tracked

        tracked_data = self.tracked_users[user_id]
        old_status = tracked_data["status"]
        new_status = str(after.status)
        start_time = datetime.fromisoformat(tracked_data.get("start_time", datetime.utcnow().isoformat()))

        # Only process if the actual status changed
        if old_status == new_status:
            return

        # Implement debounce mechanism
        now = datetime.utcnow()
        if user_id in self.recent_updates:
            last_update = self.recent_updates[user_id]
            if (now - last_update).total_seconds() < 1:  # 1-second debounce
                return

        # Update the last processed time
        self.recent_updates[user_id] = now

        # Calculate elapsed time
        elapsed = now - start_time
        elapsed_str = str(timedelta(seconds=elapsed.total_seconds())).split(".")[0]  # Format elapsed time

        # Determine the notification channel
        channel_id = tracked_data.get("channel_id", self.notification_channel)
        if channel_id:
            channel = self.bot.get_channel(channel_id)
            if channel:
                await channel.send(
                    f"`{after.name}` changed their status from `{old_status}` to `{new_status}`. "
                    f"They were in `{old_status}` for **{elapsed_str}**."
                )

        # Update the tracked status and start time
        self.tracked_users[user_id]["status"] = new_status
        self.tracked_users[user_id]["start_time"] = now.isoformat()
        self._save_data()

        # Clean up old entries from recent updates after 10 seconds
        await asyncio.sleep(10)
        self.recent_updates.pop(user_id, None)

async def setup(bot):
    await bot.add_cog(StatusTracker(bot))

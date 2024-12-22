import discord
from discord.ext import commands
from datetime import datetime

class StatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = {}  # Format: {user_id: {"channel_id": channel_id, "status": {"current_status": status, "start_time": datetime}}}
        self.notification_channel = None  # Default notification channel ID
        self._load_data()

    def _save_data(self):
        """Save tracked users' data to MongoDB."""
        for user_id, data in self.tracked_users.items():
            status = data["status"]
            self.bot.db["status_tracker"].update_one(
                {"user_id": user_id},
                {
                    "$set": {
                        "channel_id": data["channel_id"],
                        "status": {
                            "current_status": status["current_status"],
                            "start_time": status["start_time"].isoformat(),
                        },
                    }
                },
                upsert=True,
            )

    def _load_data(self):
        """Load tracked users' data from MongoDB."""
        self.tracked_users.clear()
        for record in self.bot.db["status_tracker"].find():
            if "user_id" in record and "channel_id" in record and "status" in record:
                status = record["status"]
                self.tracked_users[record["user_id"]] = {
                    "channel_id": record["channel_id"],
                    "status": {
                        "current_status": status["current_status"],
                        "start_time": datetime.fromisoformat(status["start_time"]),
                    },
                }

    @discord.app_commands.command(name="setstatuschannel", description="Set the default channel for status notifications.")
    async def set_status_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the default notification channel for status changes."""
        self.notification_channel = channel.id
        await interaction.response.send_message(f"Default status notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackstatus", description="Start tracking a user's status changes.")
    async def track_status(self, interaction: discord.Interaction, user: discord.User, channel: discord.TextChannel = None):
        """Start tracking a user's status changes."""
        if str(user.id) in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s status is already being tracked.", ephemeral=True)
        else:
            self.tracked_users[str(user.id)] = {
                "channel_id": channel.id if channel else self.notification_channel,
                "status": {"current_status": None, "start_time": datetime.now()},
            }
            self._save_data()
            await interaction.response.send_message(
                f"Started tracking {user.name}'s status. Notifications will be sent to {channel.mention if channel else 'the default channel.'}",
                ephemeral=True,
            )

    @discord.app_commands.command(name="untrackstatus", description="Stop tracking a user's status changes.")
    async def untrack_status(self, interaction: discord.Interaction, user: discord.User):
        """Stop tracking a user's status changes."""
        if str(user.id) in self.tracked_users:
            del self.tracked_users[str(user.id)]
            self.bot.db["status_tracker"].delete_one({"user_id": str(user.id)})
            await interaction.response.send_message(f"Stopped tracking {user.name}'s status.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)

    @discord.app_commands.command(name="listtrackedstatuses", description="List all currently tracked users and their channels.")
    async def list_tracked_statuses(self, interaction: discord.Interaction):
        """List all tracked users and their notification channels."""
        if not self.tracked_users:
            await interaction.response.send_message("No users are currently being tracked.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Tracked Users - Status",
            description="List of users currently being tracked for status changes.",
            color=discord.Color.blue(),
        )

        for user_id, data in self.tracked_users.items():
            user = self.bot.get_user(int(user_id))
            username = user.name if user else "Unknown User"
            channel = self.bot.get_channel(data["channel_id"])
            channel_name = channel.mention if channel else "Unknown Channel"
            embed.add_field(name=username, value=f"Channel: {channel_name}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Triggered when a user's presence (status) updates."""
        user_id = str(after.id)
        if user_id in self.tracked_users:
            tracked_data = self.tracked_users[user_id]
            current_status = tracked_data["status"]["current_status"]
            channel_id = tracked_data.get("channel_id", self.notification_channel)
            channel = self.bot.get_channel(channel_id)
            now = datetime.now()

            # Check if the status has changed
            new_status = str(after.status)
            if new_status != current_status:
                # Calculate duration of the previous status
                if current_status:
                    start_time = tracked_data["status"]["start_time"]
                    duration = now - start_time
                    if channel:
                        await channel.send(
                            f"`{after.name}` was **{current_status}** for {duration.seconds // 3600} hours, "
                            f"{(duration.seconds % 3600) // 60} minutes, and {duration.seconds % 60} seconds."
                        )

                # Update to the new status
                self.tracked_users[user_id]["status"] = {"current_status": new_status, "start_time": now}
                self._save_data()

                # Notify about the new status
                if channel:
                    await channel.send(f"`{after.name}` is now **{new_status}**.")

async def setup(bot):
    await bot.add_cog(StatusTracker(bot))

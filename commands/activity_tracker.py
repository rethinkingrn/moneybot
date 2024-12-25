import discord
from discord.ext import commands
from datetime import datetime, timedelta

class ActivityTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = {}  # Dictionary to hold user-specific tracking data
        self.notification_channel = None  # Default notification channel
        self.db = bot.db["activity_tracker"]  # MongoDB collection for activity tracking
        self._load_data()

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _load_data(self):
        """Load the tracked users from the database."""
        data = self.db.find_one({"setting": "activity_data"})
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
            {"setting": "activity_data"},
            {"$set": {"tracked_users": self.tracked_users, "default_channel": self.notification_channel}},
            upsert=True,
        )

    @discord.app_commands.command(name="setactivitychannel", description="Set the default channel for activity notifications.")
    @discord.app_commands.check(is_authorized_user)
    async def set_activity_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the default notification channel."""
        self.notification_channel = channel.id
        self._save_data()
        await interaction.response.send_message(f"Activity notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackactivity", description="Track a user's activity changes.")
    @discord.app_commands.check(is_authorized_user)
    async def track_activity(self, interaction: discord.Interaction, user: discord.User, channel: discord.TextChannel = None):
        """Add a user to the tracked list, optionally specifying a channel."""
        if str(user.id) in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s activity is already being tracked.", ephemeral=True)
        else:
            self.tracked_users[str(user.id)] = {
                "activities": [activity.name for activity in user.activities],
                "start_time": datetime.utcnow().isoformat(),
                "longest_session": 0,
                "channel_id": channel.id if channel else None,
            }
            self._save_data()
            channel_info = f"in {channel.mention}" if channel else "in the default notification channel"
            await interaction.response.send_message(f"Started tracking {user.name}'s activity {channel_info}.", ephemeral=True)

    @discord.app_commands.command(name="untrackactivity", description="Stop tracking a user's activity changes.")
    @discord.app_commands.check(is_authorized_user)
    async def untrack_activity(self, interaction: discord.Interaction, user: discord.User):
        """Remove a user from the tracked list."""
        if str(user.id) in self.tracked_users:
            del self.tracked_users[str(user.id)]
            self._save_data()
            await interaction.response.send_message(f"Stopped tracking {user.name}'s activity.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Triggered when a user's presence updates."""
        if str(after.id) in self.tracked_users:
            tracked_data = self.tracked_users[str(after.id)]

            # Ensure activities key exists
            if "activities" not in tracked_data:
                tracked_data["activities"] = []
                tracked_data["start_time"] = datetime.utcnow().isoformat()  # Reset start time
                self._save_data()

            old_activities = set(tracked_data["activities"])
            new_activities = set(activity.name for activity in after.activities)

            added_activities = new_activities - old_activities
            removed_activities = old_activities - new_activities

            now = datetime.utcnow()

            # Log session if activity ends
            if removed_activities:
                start_time = datetime.fromisoformat(tracked_data.get("start_time", now.isoformat()))
                elapsed = now - start_time
                elapsed_seconds = elapsed.total_seconds()

                # Update the longest session if applicable
                if elapsed_seconds > tracked_data.get("longest_session", 0):
                    tracked_data["longest_session"] = elapsed_seconds
                    longest_time = str(timedelta(seconds=elapsed_seconds)).split(".")[0]

                    # Notify about the new longest session
                    channel_id = tracked_data.get("channel_id", self.notification_channel)
                    if channel_id:
                        channel = self.bot.get_channel(channel_id)
                        if channel:
                            await channel.send(
                                f"{after.name} achieved a new longest session of **{longest_time}** on activity `{', '.join(removed_activities)}`."
                            )

                # Log session data into the database
                self.db.update_one(
                    {"user_id": str(after.id)},
                    {
                        "$push": {
                            "sessions": {
                                "activity": ", ".join(removed_activities),
                                "start_time": tracked_data["start_time"],
                                "end_time": now.isoformat(),
                                "duration": elapsed_seconds,
                            }
                        }
                    },
                    upsert=True,
                )

            # If activities have changed, update them and reset the start time
            if added_activities or removed_activities:
                tracked_data["activities"] = list(new_activities)
                tracked_data["start_time"] = now.isoformat()
                self._save_data()
    @discord.app_commands.command(name="activityleaderboard", description="Show the leaderboard for the longest activity sessions.")
    @discord.app_commands.check(is_authorized_user)
    async def activity_leaderboard(self, interaction: discord.Interaction):
        """Display a leaderboard of the longest activity sessions."""
        if not self.tracked_users:
            await interaction.response.send_message("No activity data available for the leaderboard.", ephemeral=True)
            return

        leaderboard = []
        for user_id, data in self.tracked_users.items():
            longest_session = data.get("longest_session", 0)
            if longest_session > 0:
                user = self.bot.get_user(int(user_id)) or await self.bot.fetch_user(int(user_id))
                leaderboard.append((user.name, longest_session))

        # Sort leaderboard by session duration in descending order
        leaderboard.sort(key=lambda x: x[1], reverse=True)

        embed = discord.Embed(
            title="Activity Leaderboard",
            description="Top users with the longest activity sessions.",
            color=discord.Color.gold(),
        )

        for rank, (user_name, duration) in enumerate(leaderboard[:10], start=1):  # Top 10
            formatted_duration = str(timedelta(seconds=duration)).split(".")[0]
            embed.add_field(name=f"#{rank} {user_name}", value=f"Longest Session: {formatted_duration}", inline=False)

        await interaction.response.send_message(embed=embed)

    @discord.app_commands.command(name="listtrackedactivities", description="List all tracked users and their notification channels.")
    @discord.app_commands.check(is_authorized_user)
    async def list_tracked_activities(self, interaction: discord.Interaction):
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
                value=f"Notification Channel: {channel_mention}\nLongest Session: {str(timedelta(seconds=data['longest_session'])).split('.')[0]}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(ActivityTracker(bot))

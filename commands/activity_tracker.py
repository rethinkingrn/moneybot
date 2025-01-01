import discord
from discord.ext import commands
from datetime import datetime

AUTHORIZED_USER_ID = 183743105688797184

def is_authorized_user(interaction: discord.Interaction):
    """Check if the user is authorized."""
    return interaction.user.id == AUTHORIZED_USER_ID

class ActivityTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = {}  # Format: {user_id: {"channel_id": channel_id, "activities": {activity_name: {"start_time": datetime}}}}
        self.notification_channel = None  # Default notification channel ID
        self._load_data()

    def _save_data(self):
        """Save tracked users' data to MongoDB."""
        for user_id, data in self.tracked_users.items():
            activities = {
                name: {"start_time": activity["start_time"].isoformat()}
                for name, activity in data["activities"].items()
            }
            self.bot.db["activity_tracker"].update_one(
                {"user_id": user_id},
                {"$set": {"channel_id": data["channel_id"], "activities": activities}},
                upsert=True,
            )

    def _load_data(self):
        """Load tracked users' data from MongoDB."""
        self.tracked_users.clear()
        for record in self.bot.db["activity_tracker"].find():
            if "user_id" in record and "channel_id" in record and "activities" in record:
                activities = {
                    name: {"start_time": datetime.fromisoformat(activity["start_time"])}
                    for name, activity in record["activities"].items()
                }
                self.tracked_users[record["user_id"]] = {
                    "channel_id": record["channel_id"],
                    "activities": activities,
                }

    @discord.app_commands.command(name="setactivitychannel", description="Set the default channel for activity notifications.")
    @discord.app_commands.check(is_authorized_user)
    async def set_activity_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the default notification channel for activity changes."""
        self.notification_channel = channel.id
        await interaction.response.send_message(f"Default activity notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackactivity", description="Start tracking a user's activities.")
    @discord.app_commands.check(is_authorized_user)
    async def track_activity(self, interaction: discord.Interaction, user: discord.User, channel: discord.TextChannel = None):
        """Start tracking a user's activities."""
        if str(user.id) in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s activities are already being tracked.", ephemeral=True)
        else:
            self.tracked_users[str(user.id)] = {
                "channel_id": channel.id if channel else self.notification_channel,
                "activities": {},
            }
            self._save_data()
            await interaction.response.send_message(
                f"Started tracking {user.name}'s activities. Notifications will be sent to {channel.mention if channel else 'the default channel.'}",
                ephemeral=True,
            )

    @discord.app_commands.command(name="untrackactivity", description="Stop tracking a user's activities.")
    @discord.app_commands.check(is_authorized_user)
    async def untrack_activity(self, interaction: discord.Interaction, user: discord.User):
        """Stop tracking a user's activities."""
        if str(user.id) in self.tracked_users:
            del self.tracked_users[str(user.id)]
            self.bot.db["activity_tracker"].delete_one({"user_id": str(user.id)})
            await interaction.response.send_message(f"Stopped tracking {user.name}'s activities.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)

    @discord.app_commands.command(name="listtrackedactivities", description="List all currently tracked users and their channels.")
    @discord.app_commands.check(is_authorized_user)
    async def list_tracked_activities(self, interaction: discord.Interaction):
        """List all tracked users and their notification channels."""
        if not self.tracked_users:
            await interaction.response.send_message("No users are currently being tracked.", ephemeral=True)
            return

        embed = discord.Embed(
            title="Tracked Users - Activities",
            description="List of users currently being tracked for activity changes.",
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
        """Triggered when a user's presence (activities) updates."""
        user_id = str(after.id)
        if user_id in self.tracked_users:
            tracked_data = self.tracked_users[user_id]
            channel_id = tracked_data.get("channel_id", self.notification_channel)
            channel = self.bot.get_channel(channel_id)
            now = datetime.now()

            # Process activities
            old_activities = tracked_data["activities"]
            new_activities = {
                activity.name: {"start_time": old_activities.get(activity.name, {}).get("start_time", now)}
                for activity in after.activities if activity.name
            }

            # Check for ended activities
            ended_activities = set(old_activities.keys()) - set(new_activities.keys())
            for activity_name in ended_activities:
                if activity_name in old_activities:
                    start_time = old_activities[activity_name]["start_time"]
                    duration = now - start_time
                    if channel:
                        await channel.send(
                            f"`{after.name}` stopped **{activity_name}** after "
                            f"{duration.seconds // 3600} hours, {(duration.seconds % 3600) // 60} minutes, and {duration.seconds % 60} seconds."
                        )

            # Check for started or updated activities
            for activity_name, data in new_activities.items():
                if activity_name not in old_activities:
                    # New activity
                    message = f"`{after.name}` started **{activity_name}**."
                    activity_details = self._get_activity_details(after.activities, activity_name)
                    if activity_details:
                        message += f"\n{activity_details}"
                    if channel:
                        await channel.send(message)

            # Update tracked data
            self.tracked_users[user_id]["activities"] = new_activities
            self._save_data()

    def _get_activity_details(self, activities, activity_name):
        """Extract details about a specific activity."""
        for activity in activities:
            if activity.name == activity_name:
                if isinstance(activity, discord.Spotify):
                    return (
                        f"🎵 Listening to **{activity.title}** by **{', '.join(activity.artists)}** "
                        f"on **{activity.album}**."
                    )
                elif isinstance(activity, discord.Game):
                    return f"🎮 Playing **{activity.name}**."
                elif isinstance(activity, discord.Streaming):
                    return f"📺 Streaming **{activity.name}** on **{activity.platform}**."
                elif activity.type == discord.ActivityType.custom:
                    return f"💬 Custom status: {activity.name or ''} {activity.state or ''}"
        return None


async def setup(bot):
    await bot.add_cog(ActivityTracker(bot))

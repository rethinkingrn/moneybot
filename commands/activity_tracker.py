import discord
from discord.ext import commands

class ActivityTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = {}  # Dictionary to hold user-specific tracking data
        self.notification_channel = None  # Default notification channel
        self.db = bot.db["activity_tracker"]  # MongoDB collection for activity tracking
        self._load_data()  # Load existing data from the database

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    def _save_data(self):
        """Save the tracked users to the database."""
        self.db.update_one(
            {"setting": "activity_data"},
            {"$set": {"tracked_users": self.tracked_users, "default_channel": self.notification_channel}},
            upsert=True,
        )

    def _load_data(self):
        """Load the tracked users from the database."""
        data = self.db.find_one({"setting": "activity_data"})
        if data:
            self.tracked_users = data.get("tracked_users", {})
            self.notification_channel = data.get("default_channel")

    @discord.app_commands.command(name="setactivitychannel", description="Set the default channel for activity change notifications.")
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
                "activity": None,  # Initial activity state
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
                value=f"Notification Channel: {channel_mention}",
                inline=False,
            )

        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Triggered when a user's presence updates, including activities."""
        if str(after.id) in self.tracked_users:
            print(f"Tracking presence for {after.name} ({after.id})")

            # Safely get tracked data
            tracked_data = self.tracked_users.get(str(after.id), {})
            old_activities = tracked_data.get("activities", [])

            # Collect current activities
            new_activities = []
            if after.activities:
                for activity in after.activities:
                    if isinstance(activity, discord.Spotify):
                        new_activities.append(f"Listening to **{activity.title}** by **{activity.artist}** on Spotify.")
                    elif isinstance(activity, discord.Game):
                        new_activities.append(f"Playing **{activity.name}**.")
                    elif isinstance(activity, discord.Streaming):
                        new_activities.append(f"Streaming **{activity.name}** on **{activity.platform}**.")
                    elif activity.name:
                        new_activities.append(f"Engaged in **{activity.name}**.")

            print(f"Old activities: {old_activities}")
            print(f"New activities: {new_activities}")

            # Compare and update activities
            if old_activities != new_activities:
                # Update the tracked user's activities
                self.tracked_users[str(after.id)]["activities"] = new_activities
                self._save_data()

                # Determine the notification channel
                channel_id = tracked_data.get("channel_id", self.notification_channel)
                if channel_id:
                    channel = self.bot.get_channel(channel_id)
                    if channel:
                        if new_activities:
                            # Sending message without pinging the user
                            await channel.send(f"{after.name} is now doing:\n" + "\n".join(new_activities))
                        else:
                            await channel.send(f"{after.name} has stopped all activities.")
                else:
                    print("No notification channel set.")




async def setup(bot):
    await bot.add_cog(ActivityTracker(bot))

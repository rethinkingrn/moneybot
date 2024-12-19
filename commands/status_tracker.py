import discord
from discord.ext import commands

class StatusTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = set()
        self.notification_channel = None

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    @discord.app_commands.command(name="setstatuschannel", description="Set the channel for status change notifications.")
    @discord.app_commands.check(is_authorized_user)
    async def set_status_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the notification channel."""
        self.notification_channel = channel.id
        await interaction.response.send_message(f"Status notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackstatus", description="Start tracking a user's status.")
    @discord.app_commands.check(is_authorized_user)
    async def track_status(self, interaction: discord.Interaction, user: discord.User):
        """Add a user to the tracked list."""
        if user.id in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s status is already being tracked.", ephemeral=True)
        else:
            self.tracked_users.add(user.id)
            await interaction.response.send_message(f"Started tracking {user.name}'s status.", ephemeral=True)

    @discord.app_commands.command(name="untrackstatus", description="Stop tracking a user's status.")
    @discord.app_commands.check(is_authorized_user)
    async def untrack_status(self, interaction: discord.Interaction, user: discord.User):
        """Remove a user from the tracked list."""
        if user.id in self.tracked_users:
            self.tracked_users.remove(user.id)
            await interaction.response.send_message(f"Stopped tracking {user.name}'s status.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        """Triggered when a user's status changes."""
        if after.id in self.tracked_users:
            # Get the before and after statuses
            before_status = before.status
            after_status = after.status

            if before_status != after_status:
                # Notify the configured channel
                if self.notification_channel:
                    channel = self.bot.get_channel(self.notification_channel)
                    if channel:
                        await channel.send(
                            f"{after.mention}'s status changed from **{before_status}** to **{after_status}**."
                        )
                else:
                    print("No notification channel set. Please use /setstatuschannel to configure.")

async def setup(bot):
    await bot.add_cog(StatusTracker(bot))
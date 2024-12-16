import discord
from discord.ext import commands

class AvatarTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.tracked_users = {}
        self.notification_channel = None  # Initialize the channel as None

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    @discord.app_commands.command(name="setavatarchannel", description="Set the channel for avatar change notifications.")
    @discord.app_commands.check(is_authorized_user)
    async def set_avatar_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set the notification channel."""
        self.notification_channel = channel.id  # Save the channel ID
        await interaction.response.send_message(f"Avatar notifications will be sent to {channel.mention}.", ephemeral=True)

    @discord.app_commands.command(name="trackavatar", description="Track a user's avatar changes.")
    @discord.app_commands.check(is_authorized_user)
    async def track_avatar(self, interaction: discord.Interaction, user: discord.User):
        """Add a user to the tracked list."""
        if user.id in self.tracked_users:
            await interaction.response.send_message(f"{user.name}'s avatar is already being tracked.", ephemeral=True)
        else:
            self.tracked_users[user.id] = user.display_avatar.url
            await interaction.response.send_message(f"Started tracking {user.name}'s avatar.", ephemeral=True)

    @discord.app_commands.command(name="untrackavatar", description="Stop tracking a user's avatar changes.")
    @discord.app_commands.check(is_authorized_user)
    async def untrack_avatar(self, interaction: discord.Interaction, user: discord.User):
        """Remove a user from the tracked list."""
        if user.id in self.tracked_users:
            del self.tracked_users[user.id]
            await interaction.response.send_message(f"Stopped tracking {user.name}'s avatar.", ephemeral=True)
        else:
            await interaction.response.send_message(f"{user.name} is not being tracked.", ephemeral=True)

    @commands.Cog.listener()
    async def on_user_update(self, before: discord.User, after: discord.User):
        """Triggered when a user updates their profile, including avatars."""
        if after.id in self.tracked_users:
            old_avatar = self.tracked_users[after.id]
            new_avatar = after.display_avatar.url

            if old_avatar != new_avatar:
                self.tracked_users[after.id] = new_avatar  # Update the tracked avatar

                if self.notification_channel:
                    channel = self.bot.get_channel(self.notification_channel)
                    if channel:
                        await channel.send(f"{after.mention} changed their avatar! Here is the new avatar: {new_avatar}")
                else:
                    print("No notification channel set. Please use /setavatarchannel to configure.")

async def setup(bot):
    await bot.add_cog(AvatarTracker(bot))

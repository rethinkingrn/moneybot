import discord
from discord.ext import commands
import requests
from pymongo import MongoClient
import os

class SpeechAnalyzer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo_url = os.getenv("MONGODB_URI")  # MongoDB URI from bot instance
        mongo_client = MongoClient(mongo_url)
        self.db = mongo_client["discord"]
        self.collection = self.db["messages"]  # Messages collection
        self.ollama_url = os.getenv("OLLAMA_URL")  # Ollama instance URL from bot instance

    def is_authorized_user(interaction: discord.Interaction):
        """Check if the user is authorized."""
        return interaction.user.id == 183743105688797184

    @discord.app_commands.command(name="analyze_speech", description="Analyze the speech patterns of a user based on their most recent messages.")
    @discord.app_commands.check(is_authorized_user)
    async def analyze_speech(self, interaction: discord.Interaction, user: discord.User, message_limit: int = 50):
        """
        Analyze a user's speech patterns using their most recent messages.
        Parameters:
        - `message_limit`: The maximum number of recent messages to process.
        """
        # Defer the response to allow processing time
        await interaction.response.defer()

        # Fetch the most recent messages from MongoDB
        from bson import Int64
        messages = list(
            self.collection.find({"author_id": Int64(user.id)})
            .sort("timestamp", -1)  # Sort by timestamp in descending order
            .limit(message_limit)
        )

        if not messages:
            await interaction.followup.send(f"No messages found for {user.name}.")
            return

        # Compile user messages for analysis
        content = "\n".join(msg["content"] for msg in messages if "content" in msg)
        prompt = f"Analyze this user's speech based on their most recent messages:\n\n{content}"

        # Make the API call to Ollama
        try:
            response = requests.post(
                f"{self.ollama_url}",
                json={"model": "dolphin-mistral", "prompt": prompt, "stream": False},
            )

            if response.status_code == 200:
                data = response.json()
                analysis = data.get("response", "No response received from the model.")

                # Split response if it exceeds the embed field limit
                embed_limit = 4096
                parts = [analysis[i:i+embed_limit] for i in range(0, len(analysis), embed_limit)]

                embeds = []
                for index, part in enumerate(parts):
                    embed = discord.Embed(
                        title=f"Speech Analysis for {user.name}",
                        description=part,
                        color=discord.Color.blue()
                    )
                    footer_text = f"Part {index + 1} of {len(parts)} - moneybot v0.0.6 - Stalking Sands v9"
                    embed.set_footer(text=footer_text)
                    embeds.append(embed)

                # Send the embeds
                for embed in embeds:
                    await interaction.followup.send(embed=embed)

            else:
                await interaction.followup.send(f"Failed to analyze speech. API returned {response.status_code}.")
        except requests.RequestException as e:
            await interaction.followup.send(f"An error occurred while connecting to the Ollama API: {str(e)}")


    @analyze_speech.error
    async def analyze_speech_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Handle errors for the analyze_speech command."""
        if isinstance(error, discord.app_commands.CheckFailure):
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        else:
            await interaction.followup.send("An unexpected error occurred while processing the request.")

async def setup(bot):
    await bot.add_cog(SpeechAnalyzer(bot))

import discord
from discord.ext import commands
import requests
from pymongo import MongoClient
import os
from typing import Optional

class GenerateCommand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        mongo_url = os.getenv("MONGODB_URI")
        mongo_client = MongoClient(mongo_url)
        self.db = mongo_client["discord"]
        self.collection = self.db["messages"]
        self.ollama_url = os.getenv("OLLAMA_URL")

    @discord.app_commands.command(
        name="generate", 
        description="Analyze recent messages from all users and generate a response"
    )
    async def generate_response(self, interaction: discord.Interaction, prompt: str):
        await interaction.response.defer()
        
        try:
            # Get last 50 messages from everyone
            messages = list(
                self.collection.find()
                .sort("timestamp", -1)
                .limit(100)
            )

            if not messages:
                await interaction.followup.send("No messages found in database.")
                return

            # Compile messages with author info
            content = []
            for msg in messages:
                author = self.bot.get_user(int(msg["author_id"])) or "Unknown User"
                content.append(f"{author}: {msg['content']}")
            
            full_context = "\n".join(content)
            full_prompt = (
                f"Recent messages from various users:\n\n{full_context}\n\n"
                f"Generate a response to this prompt considering the group's conversation style:\n\n{prompt}"
            )

            # Call Ollama API
            response = requests.post(
                f"{self.ollama_url}",
                json={
                    "model": "dolphin-mistral",
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.65,
                        "top_p": 0.9,
                        "max_tokens": 10000
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                generated_response = data.get("response", "No response received from the model.")

                # Create embed with server icon
                embed = discord.Embed(
                    title="😂",
                    description=generated_response,
                    color=discord.Color.red()
                )
                
                if interaction.guild:
                    embed.set_thumbnail(url=interaction.guild.icon.url)
                    embed.set_footer(
                        text=f"Generated for {interaction.guild.name}", 
                        icon_url=interaction.guild.icon.url
                    )
                
                await interaction.followup.send(embed=embed)
                
            else:
                await interaction.followup.send(f"API error: {response.status_code} - {response.text[:200]}")

        except Exception as e:
            await interaction.followup.send(f"Error: {str(e)}")

async def setup(bot):
    await bot.add_cog(GenerateCommand(bot))
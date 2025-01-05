import os
import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import re

class OllamaPrompt(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ollama_url = os.getenv("OLLAMA_URL")

    @app_commands.command(name="ollama", description="Send a prompt to the Ollama instance.")
    async def send_prompt(self, interaction: discord.Interaction, model: str, prompt: str):
        """Send a prompt to the Ollama instance."""
        if interaction.user.id != 183743105688797184:
            await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
            return

        # Defer the interaction publicly to show that the bot is processing the request
        await interaction.response.defer()

        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False  # Explicitly set stream to false
        }

        # Get the channel where the command was invoked
        channel = interaction.channel

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(self.ollama_url, json=payload) as response:
                    if response.status == 404:
                        await channel.send("Model not found. Check the Ollama instance and model name.")
                        return
                    elif response.status != 200:
                        error_text = await response.text()
                        await channel.send(f"Failed to connect to Ollama: {response.status} {error_text}")
                        return

                    data = await response.json()
                    response_text = data.get("response", "No response received.")
                    model_name = data.get("model", "Unknown model")
                    total_duration = data.get("total_duration", "N/A")

                    # Create a base embed for the response
                    embed = discord.Embed(
                        title="Ollama Response",
                        color=discord.Color.blue()
                    )
                    embed.add_field(name="Model", value=model_name, inline=False)
                    embed.add_field(name="Total Duration (ns)", value=total_duration, inline=False)

                    # Split the response if it exceeds the character limit for embed fields
                    max_field_length = 1024  # Discord embed field character limit

                    # Split the response into chunks
                    response_chunks = [response_text[i:i + max_field_length] for i in range(0, len(response_text), max_field_length)]

                    # Send the initial embed with model and duration as a base message
                    await channel.send(embed=embed)

                    # Process each chunk
                    for chunk in response_chunks:
                        # Split the chunk into code and non-code parts
                        code_parts = re.findall(r'```([a-zA-Z0-9]+)(.*?)```', chunk, re.DOTALL)  # Matches code blocks with language identifier
                        normal_parts = re.split(r'```([a-zA-Z0-9]+)(.*?)```', chunk)  # Splits around the code blocks

                        # Create an embed for each chunk
                        chunk_embed = discord.Embed(
                            title="Ollama Response (Continued)",
                            color=discord.Color.blue()
                        )

                        # Add normal text parts and code blocks
                        for normal, code in zip(normal_parts, code_parts):
                            # Add normal text (without code block)
                            if normal:
                                chunk_embed.add_field(name="Response", value=normal, inline=False)
                            # Add code block (with triple backticks and language for syntax highlighting)
                            if code:
                                language = code[0]
                                code_content = code[1]
                                chunk_embed.add_field(name="Code", value=f"```{language}\n{code_content}```", inline=False)

                        # If there's any remaining non-code text after the last code block
                        if len(normal_parts) > len(code_parts):
                            chunk_embed.add_field(name="Response", value=normal_parts[-1], inline=False)

                        # Send the chunk embed
                        await channel.send(embed=chunk_embed)

            except aiohttp.ClientError as e:
                await channel.send(f"Failed to connect to Ollama: {e}")

async def setup(bot):
    await bot.add_cog(OllamaPrompt(bot))

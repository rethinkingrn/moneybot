import discord
from discord import app_commands
from discord.ext import commands
from ddgs import DDGS

class GoogleSearch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="google", description="Search Google and get results")
    @app_commands.describe(query="What do you want to search for?")
    async def google(self, interaction: discord.Interaction, query: str):
        """Search the web and return results"""
        
        await interaction.response.defer()
        
        try:
            # Perform the search
            search_results = await self.perform_search(query)
            
            if not search_results:
                await interaction.followup.send("No results found.")
                return
            
            # Create an embed with the results
            embed = discord.Embed(
                title=f"🔍 Search Results: {query}",
                color=discord.Color.blue()
            )
            
            # Add up to 5 results
            for i, result in enumerate(search_results[:5], 1):
                title = result.get('title', 'No title')
                url = result.get('url', '')
                description = result.get('description', 'No description')
                
                # Truncate description if too long
                if len(description) > 350:
                    description = description[:350] + "..."
                
                embed.add_field(
                    name=f"{i}. {title}",
                    value=f"{description}\n[Read more]({url})",
                    inline=False
                )
            
            embed.set_footer(text=f"Requested by {interaction.user.display_name}")
            
            await interaction.followup.send(embed=embed)
            
        except Exception as e:
            await interaction.followup.send(f"An error occurred while searching: {str(e)}")
    
    async def perform_search(self, query: str):
        """Perform a web search using DuckDuckGo"""
        try:
            ddgs = DDGS()
            results = []
            
            # Perform the search
            search_results = ddgs.text(query, max_results=5)
            
            for r in search_results:
                results.append({
                    'title': r.get('title', 'No title'),
                    'url': r.get('href', ''),
                    'description': r.get('body', 'No description')
                })
            
            return results
        except Exception as e:
            print(f"Search error: {e}")
            return []

async def setup(bot):
    await bot.add_cog(GoogleSearch(bot))
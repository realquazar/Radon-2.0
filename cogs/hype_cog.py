import nextcord
from nextcord.ext import commands

class HypeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="hype", description="Get the official Radon workout playlist")
    async def hype(self, interaction: nextcord.Interaction):
        playlist_url = "https://music.youtube.com/playlist?list=PLiOIgEQJFWM75NepWUZEVG8U2fKhqRoOf"
        
        embed = nextcord.Embed(
            title="🔥 Radon Hype Mix",
            description="Fuel your workout with the official training playlist.",
            color=0xFF0000
        )
        
        embed.add_field(
            name="Listen on YouTube Music", 
            value=f"[Click here to start the grind]({playlist_url})", 
            inline=False
        )
        
        embed.set_footer(text="No excuses. Let's get to work.")
                
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(HypeCog(bot))
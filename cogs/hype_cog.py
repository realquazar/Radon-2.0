import nextcord
from nextcord.ext import commands

class HypeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="hype", description="Get some gym/work out song recommendations")
    async def hype(self, interaction: nextcord.Interaction):
        # Amethyst Purple Branding
        embed = nextcord.Embed(
            title="🔥 Phase: Beast Mode",
            description="✨ *'No pain, no gain!'*\n\n🎧 **2026 Hits:** *Impact* - Godmode",
            color=0x9B59B6
        )
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(HypeCog(bot))
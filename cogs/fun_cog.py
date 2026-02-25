import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Button
import random
import aiohttp

class RPSView(View):
    def __init__(self, user):
        super().__init__(timeout=30)
        self.user = user

    async def resolve_game(self, interaction: nextcord.Interaction, user_choice):
        if interaction.user != self.user:
            return await interaction.response.send_message("This isn't your game!", ephemeral=True)

        choices = ["Rock", "Paper", "Scissors"]
        bot_choice = random.choice(choices)
                
        if user_choice == bot_choice:
            result = "It's a **Tie**! 🤝"
        elif (user_choice == "Rock" and bot_choice == "Scissors") or \
             (user_choice == "Paper" and bot_choice == "Rock") or \
             (user_choice == "Scissors" and bot_choice == "Paper"):
            result = "You **Won**! 🎉"
        else:
            result = "You **Lost**! 💀"

        embed = nextcord.Embed(title="Rock Paper Scissors", color=0x3498db)
        embed.add_field(name="Your Choice", value=user_choice, inline=True)
        embed.add_field(name="Radon's Choice", value=bot_choice, inline=True)
        embed.description = f"### {result}"
        
        await interaction.response.edit_message(embed=embed, view=None)

    @nextcord.ui.button(label="Rock", emoji="🪨", style=nextcord.ButtonStyle.gray)
    async def rock(self, b, i): await self.resolve_game(i, "Rock")

    @nextcord.ui.button(label="Paper", emoji="📜", style=nextcord.ButtonStyle.gray)
    async def paper(self, b, i): await self.resolve_game(i, "Paper")

    @nextcord.ui.button(label="Scissors", emoji="✂️", style=nextcord.ButtonStyle.gray)
    async def scissors(self, b, i): await self.resolve_game(i, "Scissors")


class FunCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="rps", description="Play Rock Paper Scissors with Radon")
    async def rps(self, interaction: nextcord.Interaction):
        view = RPSView(interaction.user)
        embed = nextcord.Embed(title="Rock Paper Scissors", description="Choose your weapon below!", color=0x3498db)
        await interaction.response.send_message(embed=embed, view=view)

    
    @nextcord.slash_command(name="meme", description="Radon fetches a fresh meme for you")
    async def meme(self, interaction: nextcord.Interaction):
        
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meme-api.com/gimme") as resp:
                if resp.status != 200:
                    return await interaction.send("Failed to fetch meme. Try again later.")
                data = await resp.json()
                
                embed = nextcord.Embed(title=data['title'], url=data['postLink'], color=0xf1c40f)
                embed.set_image(url=data['url'])
                embed.set_footer(text=f"From r/{data['subreddit']}")
                await interaction.response.send_message(embed=embed)

    
    @nextcord.slash_command(name="8ball", description="Ask the magic 8-ball a question")
    async def eightball(self, interaction: nextcord.Interaction, question: str):
        responses = [
            "Yes, obviously.", "My sources say... maybe. If you stop being annoying.",
            "Ask again when you've gained some muscle.", "Don't count on it, buddy.",
            "Signs point to yes.", "Cannot predict now, I'm at the gym.",
            "Outlook not so good.", "Very doubtful.", "Yes, but it'll cost you."
        ]
        embed = nextcord.Embed(title="🎱 The Snarky 8-Ball", color=0x2c3e50)
        embed.add_field(name="Question", value=question, inline=False)
        embed.add_field(name="Radon's Answer", value=random.choice(responses), inline=False)
        await interaction.response.send_message(embed=embed)

    
    @nextcord.slash_command(name="dad_joke", description="Get a painful dad joke")
    async def dad_joke(self, interaction: nextcord.Interaction):
        async with aiohttp.ClientSession() as session:
            headers = {"Accept": "application/json"}
            async with session.get("https://icanhazdadjoke.com/", headers=headers) as resp:
                if resp.status != 200:
                    return await interaction.send("I'm not in a funny mood right now.")
                data = await resp.json()
                await interaction.response.send_message(f"🧔 | {data['joke']}")

def setup(bot):
    bot.add_cog(FunCog(bot))
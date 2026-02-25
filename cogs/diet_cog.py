import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Select, Button
import os

# --- DATA ---
FOOD_DATA = [
    {"name": "Whey Protein", "protein": 80, "calories": 400},
    {"name": "Casein Protein", "protein": 75, "calories": 370},
    {"name": "Chicken Breast", "protein": 31, "calories": 165},
    {"name": "Turkey Breast", "protein": 29, "calories": 135},
    {"name": "Bison", "protein": 28, "calories": 146},
    {"name": "Tuna (Canned)", "protein": 26, "calories": 116},
    {"name": "Lean Ground Beef", "protein": 26, "calories": 250},    
    {"name": "Salmon", "protein": 25, "calories": 208},
    {"name": "Seitan", "protein": 25, "calories": 141},
    {"name": "Peanut Butter", "protein": 25, "calories": 588},
    {"name": "Shrimp", "protein": 24, "calories": 99},
    {"name": "Almonds", "protein": 21, "calories": 579},
    {"name": "Cod", "protein": 20, "calories": 82},
    {"name": "Tempeh", "protein": 19, "calories": 192},
    {"name": "Chickpeas", "protein": 19, "calories": 364},
    {"name": "Whole Eggs", "protein": 13, "calories": 155},
    {"name": "Oats", "protein": 13, "calories": 389},
    {"name": "Cottage Cheese", "protein": 11, "calories": 82},
    {"name": "Edamame", "protein": 11, "calories": 122},
    {"name": "Egg Whites", "protein": 11, "calories": 52},
    {"name": "Greek Yogurt", "protein": 10, "calories": 59},
    {"name": "Tofu (Firm)", "protein": 10, "calories": 83},
    {"name": "Lentils", "protein": 9, "calories": 116},
    {"name": "Quinoa", "protein": 4, "calories": 120}
]

class DietView(View):
    def __init__(self, data, sort_type):
        super().__init__(timeout=60)
        self.data = data
        self.sort_type = sort_type
        self.page = 0
        self.per_page = 10
        self.max_pages = (len(data) - 1) // self.per_page

    def create_embed(self):
        title = "🥩 High Protein Rankings" if self.sort_type == "protein" else "🥗 Low Calorie Rankings"
        color = 0xE74C3C if self.sort_type == "protein" else 0x2ECC71
        
        start = self.page * self.per_page
        end = start + self.per_page
        current_items = self.data[start:end]

        embed = nextcord.Embed(title=title, color=color)
        embed.set_thumbnail(url="attachment://food.png") # Set the local thumbnail
        embed.set_footer(text=f"Page {self.page + 1} of {self.max_pages + 1} | Portions per 100g")

        description = ""
        for i, food in enumerate(current_items, start + 1):
            if self.sort_type == "protein":
                description += f"**{i}. {food['name']}**\n└ **{food['protein']}g Protein** | {food['calories']} kcal\n\n"
            else:
                description += f"**{i}. {food['name']}**\n└ **{food['calories']} kcal** | {food['protein']}g protein\n\n"
        
        embed.description = description
        return embed

    @nextcord.ui.button(label="Back", style=nextcord.ButtonStyle.gray)
    async def back(self, button, interaction):
        if self.page > 0:
            self.page -= 1
            file = nextcord.File("assets/food.png", filename="food.png")
            await interaction.response.edit_message(embed=self.create_embed(), view=self, file=file)

    @nextcord.ui.button(label="Next", style=nextcord.ButtonStyle.gray)
    async def next(self, button, interaction):
        if self.page < self.max_pages:
            self.page += 1
            file = nextcord.File("assets/food.png", filename="food.png")
            await interaction.response.edit_message(embed=self.create_embed(), view=self, file=file)

class DietDropdown(Select):
    def __init__(self):
        options = [
            nextcord.SelectOption(label="Sort by Protein", emoji="🥩", value="protein"),
            nextcord.SelectOption(label="Sort by Calories", emoji="🥗", value="calories"),
        ]
        super().__init__(placeholder="How do you want to sort?", options=options)

    async def callback(self, interaction: nextcord.Interaction):
        sort_type = self.values[0]
        if sort_type == "protein":
            sorted_data = sorted(FOOD_DATA, key=lambda x: x["protein"], reverse=True)
        else:
            sorted_data = sorted(FOOD_DATA, key=lambda x: x["calories"])
        
        file = nextcord.File("assets/food.png", filename="food.png")
        view = DietView(sorted_data, sort_type)
        await interaction.response.edit_message(embed=view.create_embed(), view=view, file=file)

class DietCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @nextcord.slash_command(name="diet", description="Browse nutritional data with a food guide")
    async def diet(self, interaction: nextcord.Interaction):
        view = View()
        view.add_item(DietDropdown())
        
        embed = nextcord.Embed(
            title="🍽️ The Gladiator Kitchen",
            description="Select a sorting method to see the best fuel for your gains.",
            color=0x9B59B6
        )
        
        # Initial image for the starting message
        file = nextcord.File("assets/food.png", filename="food.png")
        embed.set_thumbnail(url="attachment://food.png")
        
        await interaction.response.send_message(embed=embed, view=view, file=file, ephemeral=True)

def setup(bot):
    bot.add_cog(DietCog(bot))
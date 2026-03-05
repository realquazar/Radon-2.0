import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Modal, TextInput, Button
import motor.motor_asyncio
import os


class AddWorkoutModal(Modal):
    def __init__(self, cog, view_ref=None):
        super().__init__("Add Custom Exercise")
        self.cog = cog
        self.view_ref = view_ref
        self.exercise = TextInput(label="Exercise Name", placeholder="e.g. Weighted Pullups")
        self.reps = TextInput(label="Sets/Reps or Time", placeholder="e.g. 4x10")
        self.add_item(self.exercise)
        self.add_item(self.reps)

    async def callback(self, interaction: nextcord.Interaction):        
        new_entry = {"exercise": f"🧩 {self.exercise.value}", "reps": self.reps.value}
        await self.cog.collection.update_one(
            {"_id": interaction.user.id}, 
            {"$push": {"workouts": new_entry}}, 
            upsert=True
        )
        
        if self.view_ref:
            user_data = await self.cog.collection.find_one({"_id": interaction.user.id})
            self.view_ref.data = user_data.get("workouts", []) if user_data else []
            self.view_ref.update_pages()
                        
            file = nextcord.File("assets/armor.jpg", filename="armor.jpg")
            await interaction.response.edit_message(embed=self.view_ref.create_embed(), view=self.view_ref, file=file)


class CustomWorkoutView(View):
    def __init__(self, user_name, data, cog):
        super().__init__(timeout=180)
        self.user_name = user_name
        self.data = data
        self.cog = cog
        self.page = 0
        self.per_page = 5
        self.update_pages()

    def update_pages(self):
        self.max_pages = (len(self.data) - 1) // self.per_page if self.data else 0

    def create_embed(self):
        embed = nextcord.Embed(
            title=f"🛡️ {self.user_name}'s Private Armory", 
            color=0x3498db,
            description="Your custom-crafted routine. Stay shielded, stay strong."
        )
        
        embed.set_thumbnail(url="attachment://armor.jpg")
        embed.set_footer(text=f"Page {self.page + 1} of {self.max_pages + 1}")
        
        start = self.page * self.per_page
        current_list = self.data[start:start + self.per_page]
        
        if not self.data:
            embed.add_field(name="Empty", value="Click **Add** to forge your first exercise.")
        else:
            for i, w in enumerate(current_list, 1):
                embed.add_field(name=f"**{start + i}. {w['exercise']}**", value=f"└ {w['reps']}", inline=False)
        return embed

    @nextcord.ui.button(label="⬅️", style=nextcord.ButtonStyle.blurple)
    async def back(self, b, r):
        self.page = max(0, self.page - 1)
        file = nextcord.File("assets/armor.jpg", filename="armor.jpg")
        await r.response.edit_message(embed=self.create_embed(), view=self, file=file)

    @nextcord.ui.button(label="➡️", style=nextcord.ButtonStyle.blurple)
    async def forward(self, b, r):
        self.page = min(self.max_pages, self.page + 1)
        file = nextcord.File("assets/armor.jpg", filename="armor.jpg")
        await r.response.edit_message(embed=self.create_embed(), view=self, file=file)

    @nextcord.ui.button(label="Add", style=nextcord.ButtonStyle.success)
    async def add(self, b, r): await r.response.send_modal(AddWorkoutModal(self.cog, self))

    @nextcord.ui.button(label="Delete", style=nextcord.ButtonStyle.danger)
    async def delete(self, b, r):        
        pass 

    @nextcord.ui.button(label="Clear All", style=nextcord.ButtonStyle.danger)
    async def clear(self, b, r):
        await self.cog.collection.update_one({"_id": r.user.id}, {"$set": {"workouts": []}})
        self.data, self.page, self.max_pages = [], 0, 0
        file = nextcord.File("assets/armor.jpg", filename="armor.jpg")
        await r.response.edit_message(embed=self.create_embed(), view=self, file=file)


class CustomWorkoutCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cluster = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.collection = self.cluster["GymBotDB"]["custom_workouts"]

    @nextcord.slash_command(name="myworkout", description="View/Edit your custom private workout list")
    async def myworkout(self, interaction: nextcord.Interaction):
        user_data = await self.collection.find_one({"_id": interaction.user.id})
        data = user_data.get("workouts", []) if user_data else []
                
        file = nextcord.File("assets/armor.jpg", filename="armor.jpg")
        view = CustomWorkoutView(interaction.user.display_name, data, self)
        
        await interaction.response.send_message(
            embed=view.create_embed(), 
            view=view, 
            file=file, 
            ephemeral=True
        )

def setup(bot):
    bot.add_cog(CustomWorkoutCog(bot))
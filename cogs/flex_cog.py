import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Modal, TextInput
import motor.motor_asyncio
import os

class FlexModal(Modal):
    def __init__(self, cog, view_ref=None):
        super().__init__("Add Progress")
        self.cog = cog
        self.view_ref = view_ref
        self.exercise = TextInput(label="Exercise/Skill", placeholder="e.g. Planche hold")
        self.stat = TextInput(label="Result", placeholder="e.g. 15 seconds")
        self.add_item(self.exercise)
        self.add_item(self.stat)

    async def callback(self, interaction: nextcord.Interaction):
        new_entry = {"exercise": self.exercise.value, "stat": self.stat.value}
        await self.cog.collection.update_one({"_id": interaction.user.id}, {"$push": {"flexes": new_entry}}, upsert=True)
        
        if self.view_ref:
            user_data = await self.cog.collection.find_one({"_id": interaction.user.id})
            self.view_ref.data = user_data.get("flexes", []) if user_data else []
            self.view_ref.update_pages()
            
            file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
            await interaction.response.edit_message(embed=self.view_ref.create_embed(), view=self.view_ref, file=file)
        else:
            await interaction.response.send_message(f"💪 Recorded: {self.exercise.value}!", ephemeral=True)

class DeleteModal(Modal):
    def __init__(self, cog, view_ref):
        super().__init__("Delete a Flex")
        self.cog = cog
        self.view_ref = view_ref
        self.number = TextInput(label="Flex Number", placeholder="e.g. 1")
        self.add_item(self.number)

    async def callback(self, interaction: nextcord.Interaction):
        val = self.number.value.strip()
        if not val.isdigit():
            return await interaction.response.send_message("❌ Numbers only!", ephemeral=True)
        
        idx = int(val) - 1
        
        if await self.cog.delete_one_flex(interaction.user.id, idx):
            user_data = await self.cog.collection.find_one({"_id": interaction.user.id})
            self.view_ref.data = user_data.get("flexes", []) if user_data else []
            self.view_ref.update_pages()
            
            file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
            await interaction.response.edit_message(embed=self.view_ref.create_embed(), view=self.view_ref, file=file)
        else:
            await interaction.response.send_message("❌ Number not found.", ephemeral=True)


class FlexPaginationView(View):
    def __init__(self, owner_id, user_name, data, cog):
        super().__init__(timeout=120)
        self.owner_id = owner_id
        self.user_name = user_name
        self.data = data
        self.cog = cog
        self.page = 0
        self.per_page = 4
        self.update_pages()

    
    def update_pages(self):
        self.max_pages = (len(self.data) - 1) // self.per_page if self.data else 0

    def create_embed(self):
        embed = nextcord.Embed(title=f"👾 {self.user_name}'s Flex Log", color=0x9B59B6)
        embed.set_thumbnail(url="attachment://knight.png")
        embed.set_footer(text=f"Page {self.page + 1} of {self.max_pages + 1}")
        
        start = self.page * self.per_page
        current_list = self.data[start:start + self.per_page]
        for i, f in enumerate(current_list, 1):
            embed.add_field(name=f"**{start + i}. {f['exercise']}**", value=f"🧩 {f['stat']}", inline=False)
        
        if not self.data: embed.description = "No flexes yet."
        return embed

    @nextcord.ui.button(label="⬅️", style=nextcord.ButtonStyle.blurple)
    async def back(self, btn, req):        
        self.page = max(0, self.page - 1)
        file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
        await req.response.edit_message(embed=self.create_embed(), view=self, file=file)

    @nextcord.ui.button(label="➡️", style=nextcord.ButtonStyle.blurple)
    async def forward(self, btn, req):        
        self.page = min(self.max_pages, self.page + 1)
        file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
        await req.response.edit_message(embed=self.create_embed(), view=self, file=file)

    @nextcord.ui.button(label="Add", style=nextcord.ButtonStyle.success)
    async def add(self, btn, req):         
        if req.user.id != self.owner_id:
            return await req.response.send_message("❌ Only the owner can add entries!", ephemeral=True)
        await req.response.send_modal(FlexModal(self.cog, self))

    @nextcord.ui.button(label="Delete", style=nextcord.ButtonStyle.danger)
    async def delete(self, btn, req):         
        if req.user.id != self.owner_id:
            return await req.response.send_message("❌ Only the owner can delete entries!", ephemeral=True)
        await req.response.send_modal(DeleteModal(self.cog, self))

    @nextcord.ui.button(label="Clear All", style=nextcord.ButtonStyle.danger)
    async def clear(self, btn, req):        
        if req.user.id != self.owner_id:
            return await req.response.send_message("❌ Only the owner can clear the log!", ephemeral=True)
        
        await self.cog.clear_all_flexes(req.user.id)
        self.data, self.page, self.max_pages = [], 0, 0
        file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
        await req.response.edit_message(embed=self.create_embed(), view=self, file=file)


class FlexCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cluster = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.collection = self.cluster["GymBotDB"]["user_flexes"]

    
    async def delete_one_flex(self, user_id, index):
        user_data = await self.collection.find_one({"_id": user_id})
        if user_data and "flexes" in user_data:
            flexes = user_data["flexes"]
            if 0 <= index < len(flexes):
                flexes.pop(index)
                await self.collection.update_one({"_id": user_id}, {"$set": {"flexes": flexes}})
                return True
        return False

    async def clear_all_flexes(self, user_id):
        await self.collection.update_one({"_id": user_id}, {"$set": {"flexes": []}})

    @nextcord.slash_command(name="flex", description="Show your progress log")
    async def flex(self, interaction: nextcord.Interaction):
        user_data = await self.collection.find_one({"_id": interaction.user.id})
        data = user_data.get("flexes", []) if user_data else []
        
        view = FlexPaginationView(interaction.user.id, interaction.user.display_name, data, self)
        
        try:
            file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
        except FileNotFoundError:            
            return await interaction.response.send_message("❌ Error: assets/knight.png missing!", ephemeral=True)

        await interaction.response.send_message(embed=view.create_embed(), view=view, file=file)

def setup(bot):
    bot.add_cog(FlexCog(bot))

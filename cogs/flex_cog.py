import nextcord
from nextcord.ext import commands
from nextcord.ui import View, Modal, TextInput
import motor.motor_asyncio
import os
import re
import io
from datetime import datetime
import matplotlib.pyplot as plt


def normalize_name(name):
    """Removes spaces, dashes, and makes lowercase for matching."""
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

def extract_number(stat_str):
    """Extracts the first number found in a string (e.g., '15 seconds' -> 15.0)."""
    match = re.search(r"[-+]?\d*\.\d+|\d+", stat_str)
    return float(match.group()) if match else 0.0

def get_date_string():
    """Returns a formatted date like 'March 3rd, 2026'"""
    now = datetime.now()
    day = now.day
        
    if 11 <= day <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
        
    return now.strftime(f"%B {day}{suffix}, %Y")

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
        raw_name = self.exercise.value.strip()
        norm_name = normalize_name(raw_name)
        new_stat = self.stat.value.strip()
        timestamp = get_date_string()

        user_id = interaction.user.id        
        user_doc = await self.cog.collection.find_one({"_id": user_id})
        flexes = user_doc.get("flexes", []) if user_doc else []
            
        for f in flexes:
            if normalize_name(f['exercise']) == norm_name:
                if "(archived)" not in f['exercise']:
                    f['exercise'] = f"{f['exercise']} (archived)"

        new_entry = {
            "exercise": raw_name, 
            "stat": new_stat, 
            "timestamp": timestamp
        }
        flexes.append(new_entry)
        
        await self.cog.collection.update_one(
            {"_id": user_id}, 
            {"$set": {"flexes": flexes}}, 
            upsert=True
        )
        
        if self.view_ref:            
            self.view_ref.all_raw_data = flexes 
                        
            if self.view_ref.show_archived:
                self.view_ref.data = [f for f in flexes if "(archived)" in f['exercise']]
            else:
                self.view_ref.data = [f for f in flexes if "(archived)" not in f['exercise']]
            
            self.view_ref.update_pages()
                        
            file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
            await interaction.response.edit_message(
                embed=self.view_ref.create_embed(), 
                view=self.view_ref, 
                file=file
            )
        else:
            await interaction.response.send_message(f"💪 Recorded: {raw_name}!", ephemeral=True)

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


class GraphSelect(nextcord.ui.Select):
    def __init__(self, data, cog):        
        unique_exercises = []
        seen = set()
        for f in data:            
            clean = f['exercise'].replace('(archived)', '').strip()
            norm = normalize_name(clean)
            if norm not in seen:
                unique_exercises.append(clean)
                seen.add(norm)
        
        options = [
            nextcord.SelectOption(label=ex, value=normalize_name(ex)) 
            for ex in unique_exercises[:25]
        ]
                
        if not options:
            options = [nextcord.SelectOption(label="No data", value="none")]

        super().__init__(placeholder="Choose an exercise to graph...", options=options)
        self.data = data
        self.cog = cog        

    async def callback(self, interaction: nextcord.Interaction):        
        plt.clf() 
        plt.close('all') 

        target_norm = self.values[0]
                
        history_nodes = [
            f for f in self.data 
            if normalize_name(f['exercise'].replace('(archived)', '').strip()) == target_norm
        ]

        if len(history_nodes) < 2:
            return await interaction.response.send_message(
                "📈 Add more entries for this exercise to generate a trend!", ephemeral=True
            )
        
        history_nodes.sort(key=lambda x: x.get('timestamp', '2026-01-01 00:00'))
                
        import matplotlib
        matplotlib.use('Agg') 
        
        fig, ax = plt.subplots(figsize=(8, 4))
        stats = [extract_number(f['stat']) for f in history_nodes]
        dates = [f.get('timestamp', 'N/A').split(' ')[0] for f in history_nodes]

        ax.plot(dates, stats, marker='o', color="#8637DB", linewidth=2)
        ax.set_title(f"Progress: {history_nodes[-1]['exercise'].replace('(archived)', '').strip()}")
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=25)
        plt.tight_layout()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        
        await interaction.response.send_message(
            file=nextcord.File(fp=buf, filename="progress.png")            
        )

class FlexPaginationView(View):
    def __init__(self, owner_id, user_name, data, cog, show_archived=False):
        super().__init__(timeout=120)
        self.owner_id = owner_id
        self.user_name = user_name
        self.cog = cog
        self.page = 0
        self.per_page = 4
        self.show_archived = show_archived
        self.all_raw_data = data 
        
        if self.show_archived:
            self.data = [f for f in data if "(archived)" in f['exercise']]
        else:
            self.data = [f for f in data if "(archived)" not in f['exercise']]
            
        self.update_pages()

    def update_pages(self):
        self.max_pages = (len(self.data) - 1) // self.per_page if self.data else 0

    def create_embed(self):
        mode_label = "Archived" if self.show_archived else "Active"
        embed = nextcord.Embed(title=f"👾 {self.user_name}'s {mode_label} Flexes", color=0x9B59B6)
        embed.set_thumbnail(url="attachment://knight.png")
        embed.set_footer(text=f"Page {self.page + 1} of {self.max_pages + 1}")
        
        start = self.page * self.per_page
        current_list = self.data[start:start + self.per_page]
        for i, f in enumerate(current_list, 1):
            clean_name = f['exercise'].replace('(archived)', '').strip()
            field_name = f"{start + i}) {clean_name}:"
            field_value = f"📅 {f.get('timestamp', 'Legacy Date')}\n➡️ {f['stat']}"
            embed.add_field(name=field_name, value=field_value, inline=False)
        
        if not self.data: embed.description = f"No {mode_label.lower()} flexes found."
        return embed
    
    @nextcord.ui.button(label="⬅️", style=nextcord.ButtonStyle.blurple, row=0)
    async def back(self, btn, req):        
        self.page = max(0, self.page - 1)
        await req.response.edit_message(embed=self.create_embed(), view=self, file=nextcord.File(fp="./assets/knight.png", filename="knight.png"))

    @nextcord.ui.button(label="➡️", style=nextcord.ButtonStyle.blurple, row=0)
    async def forward(self, btn, req):        
        self.page = min(self.max_pages, self.page + 1)
        await req.response.edit_message(embed=self.create_embed(), view=self, file=nextcord.File(fp="./assets/knight.png", filename="knight.png"))

    @nextcord.ui.button(label="Add", style=nextcord.ButtonStyle.success, row=0)
    async def add(self, btn, req):         
        if req.user.id != self.owner_id: return await req.response.send_message("❌ No permission", ephemeral=True)
        await req.response.send_modal(FlexModal(self.cog, self))

    @nextcord.ui.button(label="Delete", style=nextcord.ButtonStyle.danger, row=0)
    async def delete(self, btn, req):         
        if req.user.id != self.owner_id: return await req.response.send_message("❌ No permission", ephemeral=True)
        await req.response.send_modal(DeleteModal(self.cog, self))

    @nextcord.ui.button(label="Clear All", style=nextcord.ButtonStyle.danger, row=0)
    async def clear(self, btn, req):        
        if req.user.id != self.owner_id: return await req.response.send_message("❌ No permission", ephemeral=True)
        await self.cog.clear_all_flexes(req.user.id)
        self.data, self.page, self.max_pages = [], 0, 0
        await req.response.edit_message(embed=self.create_embed(), view=self, file=nextcord.File(fp="./assets/knight.png", filename="knight.png"))

    
    @nextcord.ui.button(label="Menu", style=nextcord.ButtonStyle.secondary, row=1)
    async def menu(self, btn, req):
        user_data = await self.cog.collection.find_one({"_id": self.owner_id})
        new_view = FlexPaginationView(self.owner_id, self.user_name, user_data.get("flexes", []) if user_data else [], self.cog, show_archived=False)
        await req.response.edit_message(embed=new_view.create_embed(), view=new_view, file=nextcord.File(fp="./assets/knight.png", filename="knight.png"))

    @nextcord.ui.button(label="Archived", style=nextcord.ButtonStyle.secondary, row=1)
    async def toggle_archived(self, btn, req):
        user_data = await self.cog.collection.find_one({"_id": self.owner_id})
        new_view = FlexPaginationView(self.owner_id, self.user_name, user_data.get("flexes", []) if user_data else [], self.cog, show_archived=True)
        await req.response.edit_message(embed=new_view.create_embed(), view=new_view, file=nextcord.File(fp="./assets/knight.png", filename="knight.png"))

    @nextcord.ui.button(label="Graph", emoji="📈", style=nextcord.ButtonStyle.secondary, row=1)
    async def graph(self, btn, req):
        
        if not self.all_raw_data or len(self.all_raw_data) == 0:
            return await req.response.send_message("❌ No data found to graph!", ephemeral=True)
                
        v = View(timeout=60)
        v.add_item(GraphSelect(self.all_raw_data, self.cog))
        
        await req.response.send_message("📊 **Select an exercise to see your progress:**", view=v)
        
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
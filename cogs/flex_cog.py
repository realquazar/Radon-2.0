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
    return re.sub(r'[^a-zA-Z0-9]', '', name).lower()

def extract_number(stat_str):
    match = re.search(r"(\d+\.?\d*)", stat_str)
    return float(match.group(1)) if match else 0.0

def get_date_string():
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
        fancy_date = get_date_string()
        graph_label = datetime.now().strftime("%b %d")
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
            "timestamp": fancy_date,
            "graph_date": graph_label,
            "raw_ts": datetime.now().isoformat()
        }
        flexes.append(new_entry)
        await self.cog.collection.update_one({"_id": user_id}, {"$set": {"flexes": flexes}}, upsert=True)
        
        if self.view_ref:            
            self.view_ref.all_raw_data = flexes 
            self.view_ref.data = [f for f in flexes if ("(archived)" in f['exercise']) == self.view_ref.show_archived]
            self.view_ref.update_pages()
            file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
            await interaction.response.edit_message(embed=self.view_ref.create_embed(), view=self.view_ref, file=file)
        else:
            await interaction.response.send_message(f"💪 Recorded: {raw_name}!", ephemeral=True)    

class DeleteModal(Modal):
    def __init__(self, cog, view_ref):
        super().__init__("Delete a Flex")
        self.cog = cog
        self.view_ref = view_ref
                
        self.number = TextInput(
            label="Flex Number", 
            placeholder='e.g. 2 or type "all" to clear everything',
            min_length=1,
            max_length=10
        )
        self.add_item(self.number)

    async def callback(self, interaction: nextcord.Interaction):
        val = self.number.value.strip().lower()
                
        if val == "all":
            await self.cog.clear_all_flexes(interaction.user.id)
            self.view_ref.all_raw_data = []
            self.view_ref.data = []
            self.view_ref.update_pages()
            
            file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
            return await interaction.response.edit_message(
                content="🗑 All flexes have been cleared.",
                embed=self.view_ref.create_embed(), 
                view=self.view_ref, 
                file=file
            )
        
        if not val.isdigit():
            return await interaction.response.send_message('❌ Please enter a number or "all".', ephemeral=True)
        
        display_idx = int(val) - 1
        if display_idx < 0 or display_idx >= len(self.view_ref.data):
            return await interaction.response.send_message("❌ Invalid number.", ephemeral=True)
        
        target_to_delete = self.view_ref.data[display_idx]
        if await self.cog.delete_specific_flex(interaction.user.id, target_to_delete):
            user_data = await self.cog.collection.find_one({"_id": interaction.user.id})
            new_raw_data = user_data.get("flexes", []) if user_data else []
            
            self.view_ref.all_raw_data = new_raw_data
            self.view_ref.data = [f for f in new_raw_data if ("(archived)" in f['exercise']) == self.view_ref.show_archived]
            self.view_ref.update_pages()
            
            file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
            await interaction.response.edit_message(embed=self.view_ref.create_embed(), view=self.view_ref, file=file)
        else:
            await interaction.response.send_message("❌ Error deleting item.", ephemeral=True)


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
        options = [nextcord.SelectOption(label=ex, value=normalize_name(ex)) for ex in unique_exercises[:25]]
        if not options: options = [nextcord.SelectOption(label="No data", value="none")]
        super().__init__(placeholder="Choose an exercise to graph...", options=options)
        self.data, self.cog = data, cog        

    async def callback(self, interaction: nextcord.Interaction):        
        plt.close('all') 
        target_norm = self.values[0]
        history = [f for f in self.data if normalize_name(f['exercise'].replace('(archived)', '').strip()) == target_norm]
        if len(history) < 2: return await interaction.response.send_message("📈 Add more entries!", ephemeral=True)
        
        history.sort(key=lambda x: x.get('raw_ts', ''))
        import matplotlib
        matplotlib.use('Agg') 
        fig, ax = plt.subplots(figsize=(8, 4))
        stats = [extract_number(f['stat']) for f in history]
        dates = [f.get('graph_date', f.get('timestamp', 'N/A')) for f in history]
        ax.plot(dates, stats, marker='o', color="#8411FF", linewidth=2)
        ax.set_title(f"Progress: {history[-1]['exercise'].replace('(archived)', '').strip()}")
        ax.set_ylabel("Result")
        ax.set_xlabel("Date")
        ax.grid(True, linestyle='--', alpha=0.5)
        plt.xticks(rotation=25)
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close(fig)
        await interaction.response.send_message(file=nextcord.File(fp=buf, filename="progress.png"))

class FlexPaginationView(View):
    def __init__(self, owner_id, user_name, data, cog, show_archived=False):
        super().__init__(timeout=120)
        self.owner_id, self.user_name, self.cog = owner_id, user_name, cog
        self.page, self.per_page, self.show_archived = 0, 4, show_archived
        self.all_raw_data = data 
        self.data = [f for f in data if ("(archived)" in f['exercise']) == show_archived]
        self.update_pages()

    def update_pages(self):
        self.max_pages = (len(self.data) - 1) // self.per_page if self.data else 0

    def create_embed(self):
        mode = "Archived" if self.show_archived else "Active"
        embed = nextcord.Embed(title=f"👾 {self.user_name}'s {mode} Flexes", color=0x9B59B6)
        embed.set_thumbnail(url="attachment://knight.png")
        embed.set_footer(text=f"Page {self.page + 1} of {self.max_pages + 1}")
        start = self.page * self.per_page
        for i, f in enumerate(self.data[start:start + self.per_page], 1):
            name = f['exercise'].replace('(archived)', '').strip()
            embed.add_field(name=f"{start + i}) {name}:", value=f"📅 {f.get('timestamp', 'N/A')}\n➡️ {f['stat']}", inline=False)
        if not self.data: embed.description = f"No {mode.lower()} flexes found."
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

    @nextcord.ui.button(label="Menu", style=nextcord.ButtonStyle.secondary, row=1)
    async def menu(self, btn, req):
        new_view = FlexPaginationView(self.owner_id, self.user_name, self.all_raw_data, self.cog, False)
        await req.response.edit_message(embed=new_view.create_embed(), view=new_view, file=nextcord.File(fp="./assets/knight.png", filename="knight.png"))

    @nextcord.ui.button(label="Archived", style=nextcord.ButtonStyle.secondary, row=1)
    async def toggle_archived(self, btn, req):
        new_view = FlexPaginationView(self.owner_id, self.user_name, self.all_raw_data, self.cog, True)
        await req.response.edit_message(embed=new_view.create_embed(), view=new_view, file=nextcord.File(fp="./assets/knight.png", filename="knight.png"))

    @nextcord.ui.button(label="Graph", emoji="📈", style=nextcord.ButtonStyle.secondary, row=1)
    async def graph(self, btn, req):
        if not self.all_raw_data: return await req.response.send_message("❌ No data!", ephemeral=True)
        v = View(timeout=60)
        v.add_item(GraphSelect(self.all_raw_data, self.cog))
        await req.response.send_message("📊 Select an exercise:", view=v)
        
class FlexCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cluster = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.collection = self.cluster["GymBotDB"]["user_flexes"]

    async def delete_specific_flex(self, user_id, target_item):
        user_data = await self.collection.find_one({"_id": user_id})
        if user_data and "flexes" in user_data:
            flexes = user_data["flexes"]
            new_flexes = [f for f in flexes if not (f['exercise'] == target_item['exercise'] and f.get('raw_ts') == target_item.get('raw_ts'))]
            if len(new_flexes) < len(flexes):
                await self.collection.update_one({"_id": user_id}, {"$set": {"flexes": new_flexes}})
                return True
        return False
    
    async def clear_all_flexes(self, user_id):        
        await self.collection.update_one(
            {"_id": user_id}, 
            {"$set": {"flexes": []}}
        )

    @nextcord.slash_command(name="flex", description="Show progress log")
    async def flex(self, interaction: nextcord.Interaction):
        user_data = await self.collection.find_one({"_id": interaction.user.id})
        data = user_data.get("flexes", []) if user_data else []
        view = FlexPaginationView(interaction.user.id, interaction.user.display_name, data, self)
        file = nextcord.File(fp="./assets/knight.png", filename="knight.png")
        await interaction.response.send_message(embed=view.create_embed(), view=view, file=file)

def setup(bot):
    bot.add_cog(FlexCog(bot))
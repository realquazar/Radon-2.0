import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import motor.motor_asyncio
import os

class TagCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Using the same MongoDB setup as your other cogs
        self.cluster = motor.motor_asyncio.AsyncIOMotorClient(os.getenv("MONGO_URI"))
        self.db = self.cluster["RadonDB"]
        self.tags = self.db["tags"]

    @nextcord.slash_command(name="tag", description="Manage server tags")
    async def tag(self, interaction: Interaction):
        pass
    
    @tag.subcommand(name="create", description="Create a new tag")
    async def tag_create(
        self, 
        interaction: Interaction, 
        name: str = SlashOption(description="Name of the tag"), 
        content: str = SlashOption(description="What the tag should say")
    ):
        name = name.lower()
        # Check if tag exists in this guild
        existing = await self.tags.find_one({"guild_id": interaction.guild.id, "tag_name": name})
        
        if existing:
            return await interaction.response.send_message(f"❌ A tag named `{name}` already exists!", ephemeral=True)

        new_tag = {
            "guild_id": interaction.guild.id,
            "creator_id": interaction.user.id,
            "tag_name": name,
            "content": content
        }
        await self.tags.insert_one(new_tag)
        await interaction.response.send_message(f"✅ Tag `{name}` created successfully!")
    
    @tag.subcommand(name="get", description="Get a tag's content")
    async def tag_get(
        self, 
        interaction: Interaction, 
        name: str = SlashOption(description="The name of the tag to view")
    ):
        name = name.lower()
        tag_data = await self.tags.find_one({"guild_id": interaction.guild.id, "tag_name": name})
        
        if not tag_data:
            return await interaction.response.send_message(f"❌ Tag `{name}` not found.", ephemeral=True)

        await interaction.response.send_message(tag_data["content"])
    
    @tag.subcommand(name="delete", description="Delete a tag")
    async def tag_delete(
        self, 
        interaction: Interaction, 
        name: str = SlashOption(description="The name of the tag to delete")
    ):
        name = name.lower()
        tag_data = await self.tags.find_one({"guild_id": interaction.guild.id, "tag_name": name})

        if not tag_data:
            return await interaction.response.send_message(f"❌ Tag `{name}` doesn't exist.", ephemeral=True)
        
        is_moderator = interaction.user.guild_permissions.manage_messages
        if tag_data["creator_id"] != interaction.user.id and not is_moderator:
            return await interaction.response.send_message("❌ You didn't create this tag and you aren't a moderator!", ephemeral=True)

        await self.tags.delete_one({"_id": tag_data["_id"]})
        await interaction.response.send_message(f"🗑️ Tag `{name}` has been deleted.")
    
    @tag.subcommand(name="list", description="List all tags in this server")
    async def tag_list(self, interaction: Interaction):
        all_tags = self.tags.find({"guild_id": interaction.guild.id})
        tag_names = [t["tag_name"] async for t in all_tags]

        if not tag_names:
            return await interaction.response.send_message("This server has no tags yet.", ephemeral=True)

        embed = nextcord.Embed(title=f"🏷️ {interaction.guild.name} Tags", color=0x34495e)
        embed.description = ", ".join([f"`{name}`" for name in tag_names])
        await interaction.response.send_message(embed=embed)

def setup(bot):
    bot.add_cog(TagCog(bot))
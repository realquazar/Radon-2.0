import nextcord
from nextcord.ext import commands
from nextcord import Interaction, SlashOption

class ModerationCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # 1. PURGE (Delete Messages)
    @nextcord.slash_command(name="purge", description="Delete a specific number of messages")
    async def purge(
        self, 
        interaction: Interaction, 
        amount: int = SlashOption(description="Number of messages to delete", min_value=1, max_value=100)
    ):
        # Permission Check
        if not interaction.user.guild_permissions.manage_messages:
            return await interaction.response.send_message("❌ You don't have permission to manage messages!", ephemeral=True)

        await interaction.channel.purge(limit=amount)
        await interaction.response.send_message(f"🧹 Deleted `{amount}` messages.", ephemeral=True)

    # 2. KICK
    @nextcord.slash_command(name="kick", description="Kick a member from the server")
    async def kick(
        self, 
        interaction: Interaction, 
        member: nextcord.Member, 
        reason: str = SlashOption(description="Reason for the kick", default="No reason provided")
    ):
        if not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("❌ You don't have permission to kick members!", ephemeral=True)

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot kick someone with a higher or equal role!", ephemeral=True)

        await member.kick(reason=reason)
        
        embed = nextcord.Embed(title="Member Kicked", color=0xe67e22)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await interaction.response.send_message(embed=embed)

    # 3. BAN
    @nextcord.slash_command(name="ban", description="Ban a member from the server")
    async def ban(
        self, 
        interaction: Interaction, 
        member: nextcord.Member, 
        reason: str = SlashOption(description="Reason for the ban", default="No reason provided")
    ):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ You don't have permission to ban members!", ephemeral=True)

        if member.top_role >= interaction.user.top_role:
            return await interaction.response.send_message("❌ You cannot ban someone with a higher or equal role!", ephemeral=True)

        await member.ban(reason=reason)

        embed = nextcord.Embed(title="Member Banned", color=0xc0392b)
        embed.add_field(name="User", value=member.mention, inline=True)
        embed.add_field(name="Moderator", value=interaction.user.mention, inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        
        await interaction.response.send_message(embed=embed)

    # 4. UNBAN
    @nextcord.slash_command(name="unban", description="Unban a user by their User ID")
    async def unban(
        self, 
        interaction: Interaction, 
        user_id: str = SlashOption(description="The ID of the user to unban")
    ):
        if not interaction.user.guild_permissions.ban_members:
            return await interaction.response.send_message("❌ You don't have permission to unban members!", ephemeral=True)

        try:
            user = await self.bot.fetch_user(int(user_id))
            await interaction.guild.unban(user)
            await interaction.response.send_message(f"✅ Unbanned **{user.name}**.")
        except ValueError:
            await interaction.response.send_message("❌ Please provide a valid numeric User ID.", ephemeral=True)
        except nextcord.NotFound:
            await interaction.response.send_message("❌ That user was not found or isn't banned.", ephemeral=True)

def setup(bot):
    bot.add_cog(ModerationCog(bot))
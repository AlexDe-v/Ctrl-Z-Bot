import dotenv
import discord
import asyncio

from discord import ApplicationContext
from discord.commands import option

from discord.ui import View
from discord.ui import Button

client = discord.Bot(intents=discord.Intents.all())
token: str = dotenv.get_variable("./.env", "TOKEN")


@client.event
async def on_ready():
    print(f'Logged in as {client.user} on {len(client.guilds)} guilds.')

    
async def get_user(ctx: discord.AutocompleteContext):
    users = []
    entries = await ctx.interaction.guild.audit_logs(limit=300).flatten()
    for entry in entries:
        if entry.user == None:
            pass
        elif not f"{entry.user.name.lower()}#{entry.user.discriminator}" in users:
            users.append(f"{entry.user.name.lower()}#{entry.user.discriminator}")

    return [user for user in users if user.startswith(ctx.value.lower())]

@client.slash_command(description="View and undo changes from a user.")
@option("user", description="Choose a user to view and manage his changes.", autocomplete=get_user)
async def audit(ctx: ApplicationContext, user: str):
    if not ctx.author.guild_permissions.administrator:
        embed=discord.Embed(title=":x: | Admin Command", description="You have to be an administrator to run this command!", color=0xff6c6c)
        await ctx.respond(embed=embed, ephemeral=True)
        return
    if not ctx.me.guild_permissions.view_audit_log or not ctx.me.guild_permissions.manage_guild or not ctx.me.guild_permissions.moderate_members or not ctx.me.guild_permissions.manage_roles or not ctx.me.guild_permissions.manage_channels or not ctx.me.guild_permissions.ban_members:
        embed=discord.Embed(title=":x: | Missing permissions", description="The bot does not have enough permissions to do changes on this server. Make sure the bot has the following permissions: \n- view_audit_log \n- ban members \n- manage_channels \n- manage_roles", color=0xff6c6c)
        await ctx.respond(embed=embed)
        return
    entries = await ctx.interaction.guild.audit_logs(limit=300).flatten()
    user_entries = []
    for entry in entries:
        if entry.user == None:
            pass
        elif f'{entry.user.name.lower()}#{entry.user.discriminator}' == user:
            user_entries.append(entry)
    if user_entries == []:
        await ctx.interaction.response.send_message(':x: | Make sure you select a user from the dropdown.', ephemeral=True)
        return
    msg = await ctx.interaction.response.send_message(embed=discord.Embed(title="Hold on..", color=0xff80ff))
    msg = await msg.original_response()


    for index, entry in enumerate(user_entries):
        if entry.action == discord.AuditLogAction.ban:
            embed=discord.Embed(title=f":hammer: | Change review ({len(user_entries)}/{index + 1})", description=f"Action: **Member ban** \nTarget: **{entry.target}** ", color=0xff8000)
        elif entry.action == discord.AuditLogAction.channel_create:
            embed=discord.Embed(title=f":speech_left: | Change review ({len(user_entries)}/{index + 1})", description=f"Action: **Channel create** \nChannel name: **{entry.after.name}** ", color=0xff8000)
        elif entry.action == discord.AuditLogAction.channel_delete and entry.before.type.name == 'text':
            embed=discord.Embed(title=f":x: | Change review ({len(user_entries)}/{index + 1})", description=f"Action: **Text channel delete** \nChannel name: **{entry.before.name}** ", color=0xff8000)
        elif entry.action == discord.AuditLogAction.channel_delete and entry.before.type.name == 'voice':
            embed=discord.Embed(title=f":microphone2: | Change review ({len(user_entries)}/{index + 1})", description=f"Action: **Voice channel delete** \nChannel name: **{entry.before.name}** ", color=0xff8000)
        elif entry.action == discord.AuditLogAction.role_delete:
            embed=discord.Embed(title=f":x: | Change review ({len(user_entries)}/{index + 1})", description=f"Action: **Role delete** \nRole name: **{entry.before.name}** ", color=0xff8000)
        elif entry.action == discord.AuditLogAction.role_create:
            embed=discord.Embed(title=f":first_place: | Change review ({len(user_entries)}/{index + 1})", description=f"Action: **Role create** \nRole name: **{entry.after.name}** ", color=0xff8000)
        else:
            embed=discord.Embed(title=":warning: | Unsupported", description=f"This action is unsupported and cannot be undone by the bot! \nAction: **{entry.action}**")

        view = View()
        button_undo = Button(label="Undo", emoji="↩️", custom_id="undo", style=discord.ButtonStyle.blurple)
        button_undo_all = Button(label=f"Undo all {len(user_entries) - index}", style=discord.ButtonStyle.danger, custom_id="undo_all")
        button_skip = Button(label="Skip", style=discord.ButtonStyle.gray, custom_id="skip")
        view.add_item(button_undo)
        view.add_item(button_undo_all)
        view.add_item(button_skip)

        undo_all = False

        await msg.edit(view=view, embed=embed)
        def check(interaction: discord.Interaction): 
            if interaction.user.id == ctx.author.id and interaction.message.id == msg.id:
                return True
            
        
        async def undo(entry: discord.AuditLogEntry):
            if entry.action == discord.AuditLogAction.ban:
                user = await client.get_or_fetch_user(entry.target.id)
                await interaction.guild.unban(user)
            elif entry.action == discord.AuditLogAction.channel_create:
                for channel in entry.guild.channels:
                    if channel.name == entry.after.name:
                        await channel.delete(reason="Undo request")
                        break
                
            elif entry.action == discord.AuditLogAction.channel_delete and entry.before.type.name == 'text':
                overwrites_dict = {}
                for overwrite in entry.changes.before.overwrites:
                        x = overwrite[0]
                        overwrites_dict[x] = overwrite[1]
                await entry.guild.create_text_channel(entry.before.name, overwrites=overwrites_dict)
            elif entry.action == discord.AuditLogAction.channel_delete and entry.before.type.name == 'voice':
                await entry.guild.create_voice_channel(entry.before.name, overwrites=entry.before.overwrites)
            elif entry.action == discord.AuditLogAction.role_delete:
                await entry.guild.create_role(name=entry.before.name, permissions=entry.before.permissions, color=entry.before.color, mentionable=entry.before.mentionable)
            elif entry.action == discord.AuditLogAction.role_create:
                roles = await entry.guild.fetch_roles()
                for role in roles:
                    if role.name == entry.after.name:
                        await role.delete(reason=f"Undo request")
            else:
                pass
                
            

        if not undo_all:
            try:
                interaction: discord.Interaction = await client.wait_for("interaction", check=check, timeout=1000)
            except Exception:
                return
            if interaction.custom_id == "undo":
                await undo(entry=entry)
                await interaction.response.send_message(':white_check_mark:', ephemeral=True)
            elif interaction.custom_id == "undo_all":
                await msg.edit(view=view.disable_all_items())
                await interaction.response.send_message(':white_check_mark: | Wait until bot finishes undoing!', ephemeral=True)
                undo_all = True
            elif interaction.custom_id == "skip":
                await interaction.response.defer()
        else:
            undo(entry=entry)




client.run('token')
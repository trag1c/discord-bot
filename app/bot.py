import discord
from discord.ext import commands

from . import config, view
from .issues import ISSUE_REGEX, handle_issues

# Initialize our bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)


@bot.event
async def on_ready():
    print(f"Bot logged on as {bot.user}!")


@bot.event
async def on_message(message):
    # Ignore our own messages
    if message.author == bot.user:
        return

    # Special trigger command to request an invite.
    # trigger = "I WANT GHOSTTY"
    # if message.content.strip().upper() == trigger:
    #     if message.guild is None:
    #         await message.channel.send("Tell me you want me in the Ghostty server!")
    #         return
    #
    #     if message.content.strip() == trigger:
    #         # TODO
    #         return
    #
    #     await message.channel.send("Louder. LOUDER!!")
    #     return

    # Simple test
    if message.guild is None:
        if message.content == "ping":
            await message.author.send("pong")
            return

    # Look for issue numbers and link them
    if ISSUE_REGEX.search(message.content):
        await handle_issues(message)

    # Unknow message, try commands
    await bot.process_commands(message)


@bot.command()
@commands.is_owner()
async def sync(ctx: commands.Context):
    """
    Syncs all global commands.
    """
    await bot.tree.sync()
    await ctx.author.send("Command tree synced.")


@bot.tree.context_menu(name="Invite to Beta")
async def invite_member(interaction: discord.Interaction, member: discord.Member):
    """
    Adds a context menu item to a user to invite them to the beta.

    This can only be invoked by a mod.
    """
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "This command must be run from the Ghostty server, not a DM.",
            ephemeral=True,
        )
        return

    if interaction.user.get_role(config.mod_role_id) is None:
        await interaction.response.send_message(
            "You need to be an admin to add testers.", ephemeral=True
        )
        return

    if member.bot:
        await interaction.response.send_message(
            "Bots can't be testers.", ephemeral=True
        )
        return

    if member.get_role(config.tester_role_id) is not None:
        await interaction.response.send_message(
            "This user is already a tester.", ephemeral=True
        )
        return

    await member.add_roles(
        discord.Object(config.tester_role_id),
        reason="invite to beta context menu",
    )
    await member.send(view.new_tester_dm)

    await interaction.response.send_message(
        f"Added {member} as a tester.", ephemeral=True
    )


@bot.tree.command(name="invite", description="Invite a user to the beta.")
async def invite(interaction: discord.Interaction, member: discord.Member):
    """
    Same as invite_member but via a slash command.
    """
    await invite_member.callback(interaction, member)


@bot.tree.command(name="accept-invite", description="Accept a pending tester invite.")
async def accept_invite(interaction: discord.Interaction):
    """
    Accept the tester invite. This should be invoked by someone who was
    invited to the beta to complete setup with GitHub.
    """
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "This command must be run from the Ghostty server, not a DM.",
            ephemeral=True,
        )
        return

    # Verify the author is a tester
    if interaction.user.get_role(config.tester_role_id) is None:
        await interaction.response.send_message(
            "You haven't been invited to be a tester yet.", ephemeral=True
        )
        return

    # If the user already has the github role it means they already linked.
    if interaction.user.get_role(config.github_role_id) is not None:
        await interaction.response.send_message(
            view.tester_link_already, ephemeral=True
        )
        return

    # Send the tester link view
    await interaction.response.send_message(
        view.tester_accept_invite, view=view.TesterWelcome(), ephemeral=True
    )

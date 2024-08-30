from typing import cast

import discord
from discord import app_commands
from discord.ext import commands

from app import config, view
from app.issues import ISSUE_REGEX, handle_issues

# Initialize our bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents)


@bot.event
async def on_ready() -> None:
    print(f"Bot logged on as {bot.user}!")


@bot.event
async def on_message(message: discord.Message) -> None:
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
    if message.guild is None and message.content == "ping":
        await message.author.send("pong")
        return

    # Look for issue numbers and link them
    if ISSUE_REGEX.search(message.content):
        await handle_issues(message)

    # Delete non-image messages in #showcase
    if message.channel.id == config.SHOWCASE_CHANNEL_ID and not message.attachments:
        await message.delete()

    # Unknow message, try commands
    await bot.process_commands(message)


@bot.command()
@commands.is_owner()
async def sync(ctx: commands.Context) -> None:
    """
    Syncs all global commands.
    """
    await bot.tree.sync()
    await ctx.author.send("Command tree synced.")


@bot.tree.context_menu(name="Vouch for Beta")
@app_commands.checks.cooldown(1, 3600)
async def vouch_member(
    interaction: discord.Interaction, member: discord.Member
) -> None:
    """
    Adds a context menu item to a user to vouch for them to join the beta.
    """
    if not isinstance(interaction.user, discord.Member):
        await server_only_warning(interaction)
        return

    if interaction.user.get_role(config.TESTER_ROLE_ID) is None:
        await interaction.response.send_message(
            "You do not have permission to vouch for new testers.",
            ephemeral=True
        )
        return

    if member.bot:
        await interaction.response.send_message(
            "Bots can't be vouched for.", ephemeral=True
        )
        return

    if member.get_role(config.TESTER_ROLE_ID) is not None:
        await interaction.response.send_message(
            "This user is already a tester.", ephemeral=True
        )
        return

    channel = await bot.fetch_channel(config.MOD_CHANNEL_ID)
    content = (
        f"{interaction.user.mention} vouched for "
        f"{member.mention} to join the beta."
    )
    await cast(discord.TextChannel, channel).send(content)

    await interaction.response.send_message(
        f"Vouched for {member.mention} as a tester.", ephemeral=True
    )


@vouch_member.error
async def on_vouch_member_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
) -> None:
    """
    Handles the rate-limiting for the vouch command.
    """
    if isinstance(error, app_commands.CommandOnCooldown):
        content = (
            "You can only vouch for one user per hour."
            f" Try again in {error.retry_after:.0f} seconds."
        )
        await interaction.response.send_message(content, ephemeral=True)


@bot.tree.context_menu(name="Invite to Beta")
async def invite_member(
    interaction: discord.Interaction, member: discord.Member
) -> None:
    """
    Adds a context menu item to a user to invite them to the beta.

    This can only be invoked by a mod.
    """
    if not isinstance(interaction.user, discord.Member):
        await server_only_warning(interaction)
        return

    if interaction.user.get_role(config.MOD_ROLE_ID) is None:
        await interaction.response.send_message(
            "You do not have permission to invite new testers.", ephemeral=True
        )
        return

    if member.bot:
        await interaction.response.send_message(
            "Bots can't be testers.", ephemeral=True
        )
        return

    if member.get_role(config.TESTER_ROLE_ID) is not None:
        await interaction.response.send_message(
            "This user is already a tester.", ephemeral=True
        )
        return

    await member.add_roles(
        discord.Object(config.TESTER_ROLE_ID),
        reason="invite to beta context menu",
    )
    await member.send(view.NEW_TESTER_DM)

    await interaction.response.send_message(
        f"Added {member} as a tester.", ephemeral=True
    )


@bot.tree.command(name="invite", description="Invite a user to the beta.")
async def invite(interaction: discord.Interaction, member: discord.Member) -> None:
    """
    Same as invite_member but via a slash command.
    """
    await invite_member.callback(interaction, member)


@bot.tree.command(name="vouch", description="Vouch for a user to join the beta.")
@app_commands.checks.cooldown(1, 3600)
async def vouch(interaction: discord.Interaction, member: discord.User) -> None:
    """
    Same as vouch_member but via a slash command.
    """
    if not isinstance(interaction.user, discord.Member):
        await server_only_warning(interaction)
        return
    await vouch_member.callback(interaction, member)


@vouch.error
async def vouch_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    """
    Handles the rate-limiting for the vouch command.
    """
    await on_vouch_member_error(interaction, error)


@bot.tree.command(name="accept-invite", description="Accept a pending tester invite.")
async def accept_invite(interaction: discord.Interaction) -> None:
    """
    Accept the tester invite. This should be invoked by someone who was
    invited to the beta to complete setup with GitHub.
    """
    if not isinstance(interaction.user, discord.Member):
        await server_only_warning(interaction)
        return

    # Verify the author is a tester
    if interaction.user.get_role(config.TESTER_ROLE_ID) is None:
        await interaction.response.send_message(
            "You haven't been invited to be a tester yet.", ephemeral=True
        )
        return

    # If the user already has the github role it means they already linked.
    if interaction.user.get_role(config.GITHUB_ROLE_ID) is not None:
        await interaction.response.send_message(
            view.TESTER_LINK_ALREADY, ephemeral=True
        )
        return

    # Send the tester link view
    await interaction.response.send_message(
        view.TESTER_ACCEPT_INVITE, view=view.TesterWelcome(), ephemeral=True
    )


async def server_only_warning(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "This command must be run from the Ghostty server, not a DM.",
        ephemeral=True,
    )

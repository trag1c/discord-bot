from __future__ import annotations

from typing import TYPE_CHECKING, cast

import discord
from discord import app_commands

from app.setup import bot, config
from app.utils import is_mod, is_tester, server_only_warning

if TYPE_CHECKING:
    from collections.abc import Iterator

COOLDOWN_TIME = 604_800  # 1 week


def _get_members_from_interaction(
    interaction: discord.Interaction,
) -> Iterator[discord.Member]:
    if (
        not interaction.data
        or not (resolved_data := interaction.data.get("resolved", {}))
        or not (resolved_members := resolved_data.get("members", {}))
    ):
        return iter(())
    # This function is called after the DM check so
    # interaction.guild is guaranteed to be a Guild
    guild = cast(discord.Guild, interaction.guild)
    member_ids = map(int, resolved_members)
    return filter(None, map(guild.get_member, member_ids))


def can_vouch(interaction: discord.Interaction) -> app_commands.Cooldown | None:
    if (
        not isinstance(interaction.user, discord.Member)
        or not is_tester(interaction.user)
        or is_mod(interaction.user)
    ):
        return None
    target_member = next(_get_members_from_interaction(interaction))
    if target_member.bot or is_tester(target_member):
        return None
    return app_commands.Cooldown(1, COOLDOWN_TIME)


@bot.tree.context_menu(name="Vouch for Beta")
@app_commands.checks.dynamic_cooldown(can_vouch)
async def vouch_member(
    interaction: discord.Interaction, member: discord.Member
) -> None:
    """
    Adds a context menu item to a user to vouch for them to join the beta.
    """
    if not isinstance(interaction.user, discord.Member):
        await server_only_warning(interaction)
        return

    if not is_tester(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to vouch for new testers.", ephemeral=True
        )
        return

    if member.bot:
        await interaction.response.send_message(
            "Bots can't be vouched for.", ephemeral=True
        )
        return

    if is_tester(member):
        await interaction.response.send_message(
            "This user is already a tester.", ephemeral=True
        )
        return

    channel = await bot.fetch_channel(config.MOD_CHANNEL_ID)
    content = (
        f"{interaction.user.mention} vouched for {member.mention} to join the beta."
    )
    await cast(discord.TextChannel, channel).send(content)

    await interaction.response.send_message(
        f"Vouched for {member.mention} as a tester.", ephemeral=True
    )


@vouch_member.error
async def on_vouch_member_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
) -> None:
    """
    Handles the rate-limiting for the vouch command.
    """
    if isinstance(error, app_commands.CommandOnCooldown):
        content = (
            "Vouches are rate-limited per user."
            f" Try again in {error.retry_after:.0f} seconds."
        )
        await interaction.response.send_message(content, ephemeral=True)


@bot.tree.command(name="vouch", description="Vouch for a user to join the beta.")
@app_commands.checks.dynamic_cooldown(can_vouch)
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

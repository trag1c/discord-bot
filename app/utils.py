from __future__ import annotations

import discord
from typing_extensions import TypeIs

from app.setup import config


async def server_only_warning(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "This command must be run from the Ghostty server, not a DM.",
        ephemeral=True,
    )


def is_dm(user: discord.User | discord.Member) -> TypeIs[discord.User]:
    return not isinstance(user, discord.Member)


def _has_role(member: discord.Member, role_id: int) -> bool:
    return member.get_role(role_id) is not None


def is_tester(member: discord.Member) -> bool:
    return _has_role(member, config.TESTER_ROLE_ID)


def is_mod(member: discord.Member) -> bool:
    return _has_role(member, config.MOD_ROLE_ID)


def has_linked_github(member: discord.Member) -> bool:
    return _has_role(member, config.GITHUB_ROLE_ID)

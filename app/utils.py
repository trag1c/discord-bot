from __future__ import annotations

import io
from textwrap import shorten

import discord
from typing_extensions import TypeIs

from app.setup import config

MAX_ATTACHMENT_SIZE = 67_108_864  # 64 MiB


async def server_only_warning(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        "This command must be run from the Ghostty server, not a DM.",
        ephemeral=True,
    )


async def get_or_create_webhook(
    name: str, channel: discord.TextChannel
) -> discord.Webhook:
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == name:
            if webhook.token is None:
                await webhook.delete()
            else:
                return webhook

    return await channel.create_webhook(name=name)


async def move_message_via_webhook(
    webhook: discord.Webhook,
    message: discord.Message,
    executor: discord.Member | None = None,
) -> None:
    content = message.content
    uploads = []
    skipped = 0

    if message.attachments:
        # We need to store the attachments in a buffer for a reupload
        for attachment in message.attachments:
            if attachment.size > MAX_ATTACHMENT_SIZE:
                skipped += 1
                continue

            fp = io.BytesIO(await attachment.read())
            uploads.append(discord.File(fp, filename=attachment.filename))

    reactions_with_count = {}
    for reaction in message.reactions:
        emoji = reaction.emoji
        if isinstance(emoji, discord.Emoji) and not emoji.is_usable():
            continue

        if isinstance(emoji, discord.PartialEmoji):
            # TODO: Can we register the emoji with the bot temporarily?
            continue

        reactions_with_count[reaction.emoji] = reaction.count

    subtext = ""
    if reactions_with_count:
        subtext += " "
        subtext += "   ".join(
            f"x{count} {emoji}" for emoji, count in reactions_with_count.items()
        )

        subtext += "\n"

    if executor:
        subtext += f" Moved from {message.channel.mention} by {executor.mention}"
    if skipped:
        subtext += f" (skipped {skipped} large attachment(s))"
    if subtext:
        content += f"\n-#{subtext}"

    # We have validated ahead of time that this is a discord.Member
    # So we can safely access server-specific attributes
    await webhook.send(
        content=content,
        username=message.author.display_name,
        avatar_url=message.author.display_avatar.url,
        allowed_mentions=discord.AllowedMentions.none(),
        files=uploads,
    )

    await message.delete()


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


async def try_dm(user: discord.User | discord.Member, content: str) -> None:
    try:
        await user.send(content)
    except discord.Forbidden:
        print(f"Failed to DM {user} with: {shorten(content, width=50)}")

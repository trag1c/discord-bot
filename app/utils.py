from __future__ import annotations

import io

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

    if message.attachments and len(message.attachments) > 0:
        # We need to store the attachments in a buffer for a reupload
        for attachment in message.attachments:
            if attachment.size > MAX_ATTACHMENT_SIZE:
                skipped += 1
                continue

            fp = io.BytesIO(await attachment.read())
            uploads.append(discord.File(fp, filename=attachment.filename))

    if executor:
        content += f"\n-# Moved from {message.channel.mention}"
        content += f" by {executor.mention}"

    if skipped > 0:
        # Need to add this if executor is None
        # otherwise there will be no tiny footer
        if executor is None:
            content += "\n-#"

        content += f" (skipped {skipped} large attachment(s))"

    await webhook.send(
        content=content,
        username=message.author.display_name,
        avatar_url=message.author.avatar.url,
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

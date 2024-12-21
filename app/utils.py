from __future__ import annotations

import io
from collections.abc import Callable
from textwrap import shorten

import discord
from typing_extensions import TypeIs

from app.setup import config

MAX_ATTACHMENT_SIZE = 67_108_864  # 64 MiB

SERVER_ONLY = discord.app_commands.allowed_contexts(
    guilds=True, dms=False, private_channels=False
)

Account = discord.User | discord.Member


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
    thread: discord.abc.Snowflake = discord.utils.MISSING,
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
    content += "".join(f"\n-# {line.lstrip()}" for line in subtext.splitlines())

    # We have validated ahead of time that this is a discord.Member
    # So we can safely access server-specific attributes
    await webhook.send(
        content=content,
        poll=message.poll or discord.utils.MISSING,
        username=message.author.display_name,
        avatar_url=message.author.display_avatar.url,
        allowed_mentions=discord.AllowedMentions.none(),
        files=uploads,
        thread=thread,
    )

    await message.delete()


def is_dm(account: Account) -> TypeIs[discord.User]:
    return not isinstance(account, discord.Member)


def is_mod(member: discord.Member) -> bool:
    return member.get_role(config.MOD_ROLE_ID) is not None


async def try_dm(account: Account, content: str) -> None:
    try:
        await account.send(content)
    except discord.Forbidden:
        print(f"Failed to DM {account} with: {shorten(content, width=50)}")


async def _get_original_message(message: discord.Message) -> discord.Message | None:
    if (msg_ref := message.reference) is None:
        return None
    if msg_ref.cached_message is not None:
        return msg_ref.cached_message
    if (
        message.guild is None
        or msg_ref.channel_id is None
        or msg_ref.message_id is None
    ):
        return None
    if not isinstance(
        channel := message.guild.get_channel(msg_ref.channel_id), discord.TextChannel
    ):
        return None
    return await channel.fetch_message(msg_ref.message_id)


async def check_message(
    msg: discord.Message, predicate: Callable[[discord.Message], object]
) -> bool:
    """
    Checks a message and its reference chain for a predicate.
    Basically adds support for the forwarding feature.
    """
    if predicate(msg):
        return True
    if (original_msg := await _get_original_message(msg)) is None:
        return False
    return await check_message(original_msg, predicate)

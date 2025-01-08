import re
from collections.abc import Callable
from io import BytesIO
from typing import NamedTuple

import discord

from app.setup import config
from app.utils import try_dm

URL_REGEX = re.compile(
    r"https?:\/\/(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)"
)
MESSAGE_DELETION_TEMPLATE = (
    "Hey! Your message in {} was deleted because it did not contain {}."
    " Make sure to include {}, and respond in threads.\n"
    "Here's the message you tried to send:\n\n"
)
REGULAR_MESSAGE_TYPES = frozenset(
    {discord.MessageType.default, discord.MessageType.reply}
)


class MessageFilter(NamedTuple):
    channel_id: int
    filter: Callable[[discord.Message], object]
    template_fillers: tuple[str, str]


MESSAGE_FILTERS = (
    # Delete non-image messages in #showcase
    MessageFilter(
        config.SHOWCASE_CHANNEL_ID,
        lambda msg: msg.attachments,
        ("any attachments", "a screenshot or a video"),
    ),
    # Delete non-link messages in #media
    MessageFilter(
        config.MEDIA_CHANNEL_ID,
        lambda msg: URL_REGEX.search(msg.content),
        ("a link", "a link"),
    ),
)


async def check_message_filters(message: discord.Message) -> bool:
    for msg_filter in MESSAGE_FILTERS:
        if message.channel.id != msg_filter.channel_id or msg_filter.filter(message):
            continue

        await message.delete()

        # Don't DM the user if it's a system message
        # (e.g. "@user started a thread")
        if message.type not in REGULAR_MESSAGE_TYPES:
            continue

        assert isinstance(message.channel, discord.TextChannel)

        content = MESSAGE_DELETION_TEMPLATE.format(
            message.channel.mention, *msg_filter.template_fillers
        )
        if len(content + message.content) > 2000:
            attachments = [
                discord.File(BytesIO(message.content.encode()), filename="content.md")
            ]
        else:
            attachments = []
            content += message.content

        await try_dm(message.author, content, files=attachments)
        return True
    return False

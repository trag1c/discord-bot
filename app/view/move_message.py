from typing import cast

import discord

from app.setup import bot
from app.utils import get_or_create_webhook, move_message_via_webhook


class SelectChannel(discord.ui.View):
    def __init__(self, message: discord.Message, executor: discord.Member) -> None:
        super().__init__()
        self.message = message
        self.executor = executor
        self._used = False

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text, discord.ChannelType.public_thread],
        placeholder="Select a channel",
        min_values=1,
        max_values=1,
    )
    async def select_channel(
        self, interaction: discord.Interaction, sel: discord.ui.ChannelSelect
    ) -> None:
        if self._used:
            return
        self._used = True
        channel = await bot.fetch_channel(sel.values[0].id)
        if channel.id == self.message.channel.id:
            await interaction.response.send_message(
                "You can't move a message to the same channel.", ephemeral=True
            )
            return

        await interaction.response.defer(thinking=True, ephemeral=True)
        webhook_channel, thread = (
            (channel.parent, channel)
            if isinstance(channel, discord.Thread)
            else (channel, discord.utils.MISSING)
        )
        webhook = await get_or_create_webhook("Ghostty Moderator", webhook_channel)
        await move_message_via_webhook(webhook, self.message, self.executor, thread=thread)
        await interaction.followup.send(
            content=f"Moved the message to {channel.mention}.",
            view=Ghostping(
                cast(discord.Member, self.message.author),
                cast(discord.abc.Messageable, channel),
            ),
        )


class Ghostping(discord.ui.View):
    def __init__(
        self, author: discord.Member, channel: discord.abc.Messageable
    ) -> None:
        super().__init__()
        self._author = author
        self._channel = channel

    @discord.ui.button(
        label="Ghostping",
        emoji="👻",
        style=discord.ButtonStyle.secondary,
    )
    async def ghostping(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        await interaction.response.defer(ephemeral=True)
        await (await self._channel.send(self._author.mention)).delete()
        await interaction.followup.send(
            f"Ghostpinged {self._author.name}.", ephemeral=True
        )

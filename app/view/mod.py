import discord

from app.setup import bot
from app.utils import get_or_create_webhook


class SelectChannel(discord.ui.View):
    def __init__(self, message: discord.Message):
        super().__init__()
        self.message = message

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text],
        placeholder="Select a channel",
        min_values=1,
        max_values=1,
    )
    async def select_channel(
        self, interaction: discord.Interaction, sel: discord.ui.ChannelSelect
    ) -> None:
        channel = await bot.fetch_channel(sel.values[0].id)
        if channel.id == self.message.channel.id:
            await interaction.response.send_message(
                "You can't move a message to the same channel.", ephemeral=True
            )
            return

        webhook = await get_or_create_webhook("Ghostty Moderator", channel)
        content = self.message.content
        if self.message.attachments:
            content += "\n" + "\n".join(
                attachment.url for attachment in self.message.attachments
            )

        content += f"\n-# Moved from {self.message.channel.mention}"
        await webhook.send(
            content=content,
            username=self.message.author.display_name,
            avatar_url=self.message.author.avatar.url,
        )

        await self.message.delete()
        await interaction.response.send_message(
            f"Moved the message to {channel.mention}.", ephemeral=True
        )

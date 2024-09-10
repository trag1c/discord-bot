import discord
import io

from app.setup import bot
from app.utils import get_or_create_webhook

MAX_ATTACHMENT_SIZE = 67_108_864  # 64 MiB

class SelectChannel(discord.ui.View):
    def __init__(self, message: discord.Message, executor: discord.Member):
        super().__init__()
        self.message = message
        self.executor = executor

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

        uploads = []
        skipped = 0
        if self.message.attachments and len(self.message.attachments) > 0:
            # We need to store the attachments in a buffer for a reupload
            for attachment in self.message.attachments:
                if attachment.size > MAX_ATTACHMENT_SIZE:
                    skipped += 1
                    continue

                fp = io.BytesIO(await attachment.read())
                uploads.append(discord.File(fp, filename=attachment.filename))

        content += f"\n-# Moved from {self.message.channel.mention}"
        content += f" by {self.executor.mention}"

        if skipped > 0:
            content += f" (skipped {skipped} large attachments)"

        await webhook.send(
            content=content,
            username=self.message.author.display_name,
            avatar_url=self.message.author.avatar.url,
            allowed_mentions=discord.AllowedMentions.none(),
            files=uploads,
        )

        await self.message.delete()
        await interaction.response.edit_message(
            content=f"Moved the message to {channel.mention}.",
            view=None
        )

import discord


class DeleteMention(discord.ui.View):
    def __init__(self, message: discord.Message, entity_count: int) -> None:
        super().__init__()
        self.message = message
        self.plural = entity_count > 1

    @discord.ui.button(
        label="Delete",
        emoji="🗑️",
        style=discord.ButtonStyle.gray,
    )
    async def delete(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        if interaction.user.id != self.message.author.id:
            await interaction.response.send_message(
                "Only the person who mentioned "
                + ("these entities" if self.plural else "this entity")
                + " can remove this message.",
                ephemeral=True,
            )
            return
        assert interaction.message
        await interaction.message.delete()

import discord

from app import view
from app.setup import bot
from app.utils import is_dm, is_mod, server_only_warning


@bot.tree.context_menu(name="Move message")
@discord.app_commands.default_permissions(manage_messages=True)
async def move_message(
    interaction: discord.Interaction, message: discord.Message
) -> None:
    """
    Adds a context menu item to a message to move it to a different channel.
    This is used as a moderation tool to make discussion on-topic.
    """
    if is_dm(interaction.user):
        await server_only_warning(interaction)
        return

    if not is_mod(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to move messages.", ephemeral=True
        )
        return

    await interaction.response.send_message(
        "Select a channel to move this message to.",
        view=view.SelectChannel(message, executor=interaction.user),
        ephemeral=True,
    )

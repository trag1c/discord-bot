import traceback

import discord

class TesterWelcome(discord.ui.View):
    """The view shown to new testers."""

    @discord.ui.button(label='Accept and Link GitHub')
    async def link(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TesterLink())


class TesterLink(discord.ui.Modal, title='Link GitHub'):
    """The modal shown to link a GitHub account."""

    username = discord.ui.TextInput(
        label='GitHub Username',
        placeholder='@mitchellh',
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Thanks for your feedback, {self.username.value}!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)

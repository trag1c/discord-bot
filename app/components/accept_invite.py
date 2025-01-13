import discord

from app.setup import bot, config
from app.utils import SERVER_ONLY, is_dm, try_dm


@bot.tree.command(name="accept-invite", description="Accept a pending tester invite.")
@SERVER_ONLY
async def accept_invite(interaction: discord.Interaction) -> None:
    assert not is_dm(interaction.user)

    await try_dm(interaction.user, config.ACCEPT_INVITE_URL, silent=True)
    await try_dm(
        interaction.user,
        "Ghostty is already out! :point_right: https://ghostty.org/",
    )
    await interaction.response.send_message("Check your DMs!", ephemeral=True)

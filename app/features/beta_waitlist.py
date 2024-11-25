import datetime as dt
from io import BytesIO
from typing import cast

import discord

from app import view
from app.setup import bot
from app.utils import SERVER_ONLY, is_dm, is_mod, is_tester


@bot.tree.command(
    name="beta-waitlist",
    description="Show oldest N members waiting for an invite.",
)
@discord.app_commands.default_permissions(manage_messages=True)
@SERVER_ONLY
async def beta_waitlist(interaction: discord.Interaction, n: int) -> None:
    assert interaction.guild is not None

    waitlist = sorted(
        (
            member
            for member in interaction.guild.members
            if not (member.bot or member.pending or is_tester(member))
        ),
        # Apparently joined_at can be None "in certain cases" :)
        key=lambda m: cast(dt.datetime, m.joined_at),
    )[:n]

    buf = BytesIO(
        b"\n".join(
            f"{member.id},{member.name},{member.joined_at:%Y-%m-%dT%H:%M:%S}".encode()
            for member in waitlist
        )
    )
    await interaction.response.send_message(
        content=f"**Note:** Found only {len(waitlist)} entries."
        if len(waitlist) != n
        else None,
        file=discord.File(buf, f"beta-waitlist-top{n}.csv"),
    )


@bot.tree.context_menu(name="Bulk invite")
@discord.app_commands.default_permissions(manage_messages=True)
@SERVER_ONLY
async def bulk_invite(
    interaction: discord.Interaction, message: discord.Message
) -> None:
    assert not is_dm(interaction.user)

    if not is_mod(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to invite new testers.", ephemeral=True
        )
        return

    mentions = cast(list[discord.Member], message.mentions)
    prompt = f"Are you sure you want to invite {len(mentions)} members?"
    await interaction.response.send_message(
        prompt,
        view=view.ConfirmBulkInvite(mentions, message, prompt),
        ephemeral=True,
    )

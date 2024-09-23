import datetime as dt
from pathlib import Path
from typing import cast

import discord

from app.setup import bot
from app.utils import is_tester, server_only_warning


@bot.tree.command(
    name="beta-waitlist",
    description="Show oldest N members waiting for an invite.",
)
@discord.app_commands.default_permissions(manage_messages=True)
async def beta_waitlist(interaction: discord.Interaction, n: int) -> None:
    if interaction.guild is None:
        await server_only_warning(interaction)
        return

    members_iter = iter(interaction.guild.members)
    waitlist: list[discord.Member] = []
    while len(waitlist) < n and (member := next(members_iter, None)) is not None:
        if member.bot or is_tester(member):
            continue
        waitlist.append(member)

    # Apparently joined_at can be None "in certain cases" :)
    waitlist.sort(key=lambda m: cast(dt.datetime, m.joined_at))

    path = Path(filename := f"beta-waitlist-top{n}.csv")
    path.write_text(
        "\n".join(
            f"{member.name},{member.joined_at:%Y-%m-%dT%H:%M:%S}" for member in waitlist
        )
    )
    await interaction.response.send_message(
        content=f"**Note:** Found only {len(waitlist)} entries."
        if len(waitlist) != n
        else None,
        file=discord.File(path, filename),
    )
    path.unlink()

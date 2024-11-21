from __future__ import annotations

import datetime as dt
from typing import cast

import discord

from app import view
from app.db import models
from app.db.connect import Session
from app.db.utils import fetch_user
from app.setup import bot, config
from app.utils import SERVER_ONLY, Account, is_dm, is_mod, is_tester

COOLDOWN_TIME = 604_800  # 1 week


@bot.tree.context_menu(name="Check vouch blacklist")
@discord.app_commands.default_permissions(manage_messages=True)
@SERVER_ONLY
async def check_blacklist(
    interaction: discord.Interaction, member: discord.User
) -> None:
    assert not is_dm(interaction.user)

    db_user = fetch_user(member)

    await interaction.response.send_message(
        f"{member.mention} is "
        + ("not " * (not db_user.is_vouch_blacklisted))
        + "blacklisted from vouching.",
        ephemeral=True,
    )


@bot.tree.command(
    name="check-blacklist", description="Check if a user is blacklisted from vouching."
)
@discord.app_commands.default_permissions(manage_messages=True)
@SERVER_ONLY
async def check_blacklist_command(
    interaction: discord.Interaction, member: discord.User
) -> None:
    await check_blacklist.callback(interaction, member)


@bot.tree.context_menu(name="Blacklist from vouching")
@discord.app_commands.default_permissions(manage_messages=True)
@SERVER_ONLY
async def blacklist_vouch_member(
    interaction: discord.Interaction, member: discord.User
) -> None:
    assert not is_dm(interaction.user)

    if not is_mod(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to blacklist users from vouching.",
            ephemeral=True,
        )
        return

    db_user = fetch_user(member)

    with Session() as session:
        session.add(db_user)
        session.commit()

    await interaction.response.send_message(
        ("B" if db_user.is_vouch_blacklisted else "Unb")
        + f"lacklisted {member.mention}.",
        ephemeral=True,
    )


@bot.tree.command(name="blacklist-vouch", description="Blacklist a user from vouching.")
@discord.app_commands.default_permissions(manage_messages=True)
@SERVER_ONLY
async def blacklist_vouch(
    interaction: discord.Interaction, member: discord.User
) -> None:
    await blacklist_vouch_member.callback(interaction, member)


@bot.tree.context_menu(name="Vouch for Beta")
@SERVER_ONLY
async def vouch_member(
    interaction: discord.Interaction, member: discord.Member
) -> None:
    """
    Adds a context menu item to a user to vouch for them to join the beta.
    """
    assert not is_dm(interaction.user)

    if not is_tester(interaction.user):
        await interaction.response.send_message(
            "You do not have permission to vouch for new testers.", ephemeral=True
        )
        return

    if member.bot:
        await interaction.response.send_message(
            "Bots can't be vouched for.", ephemeral=True
        )
        return

    if is_tester(member):
        await interaction.response.send_message(
            "This user is already a tester.", ephemeral=True
        )
        return

    db_user = fetch_user(interaction.user)

    if db_user.tester_since is not None and (
        dt.datetime.now(tz=dt.UTC) - db_user.tester_since.replace(tzinfo=dt.UTC)
        < dt.timedelta(weeks=1)
    ):
        await interaction.response.send_message(
            "You have to be a tester for one week in order to vouch.",
            ephemeral=True,
        )
        return

    if _has_vouched_recently(interaction.user) and not is_mod(interaction.user):
        await interaction.response.send_message(
            "You can only vouch once per week.", ephemeral=True
        )
        return

    if _has_already_vouched(interaction.user):
        await interaction.response.send_message(
            "You already have a pending vouch.", ephemeral=True
        )
        return

    if _is_already_vouched_for(member):
        await interaction.response.send_message(
            "This user has already been vouched for.", ephemeral=True
        )
        return

    if fetch_user(interaction.user).is_vouch_blacklisted:
        # We're trolling the user the bot is broken
        await interaction.response.send_message(
            "Something went wrong :(", ephemeral=True
        )
        return

    channel = await bot.fetch_channel(config.VOUCH_CHANNEL_ID)
    content = (
        f"{interaction.user.mention} vouched for {member.mention} to join the beta."
    )

    with Session() as session:
        vouch_count = (
            session.query(models.Vouch)
            .filter_by(voucher_id=interaction.user.id)
            .count()
        )

        content += f" (vouch #{vouch_count + 1})"

        db_vouch = models.Vouch(
            voucher_id=interaction.user.id,
            receiver_id=member.id,
        )

        session.add(db_vouch)
        session.commit()

    msg = await cast(discord.TextChannel, channel).send(
        content=content, view=view.DecideVouch(vouch=db_vouch)
    )

    # Store the message ID so we can track this vouch later
    with Session() as session:
        db_vouch.interaction_id = msg.id
        session.add(db_vouch)
        session.commit()

    await interaction.response.send_message(
        f"Vouched for {member.mention} as a tester.", ephemeral=True
    )


@bot.tree.command(name="vouch", description="Vouch for a user to join the beta.")
@SERVER_ONLY
async def vouch(interaction: discord.Interaction, member: discord.User) -> None:
    """Same as vouch_member but via a slash command."""
    assert not is_dm(interaction.user)
    await vouch_member.callback(interaction, member)


def _is_already_vouched_for(member: discord.Member) -> bool:
    with Session() as session:
        return session.query(models.Vouch).filter_by(receiver_id=member.id).count() > 0


def _has_already_vouched(account: Account) -> bool:
    with Session() as session:
        return (
            session.query(models.Vouch)
            .filter_by(voucher_id=account.id)
            .filter_by(vouch_state=models.VouchState.PENDING)
            .count()
            > 0
        )


def _has_vouched_recently(account: Account) -> bool:
    one_week_ago = dt.datetime.now(tz=dt.UTC) - dt.timedelta(weeks=1)

    with Session() as session:
        return (
            session.query(models.Vouch)
            .filter_by(voucher_id=account.id)
            .filter(models.Vouch.vouch_state != models.VouchState.PENDING)
            .filter(models.Vouch.request_date > one_week_ago)
            .count()
            > 0
        )

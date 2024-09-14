from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import cast

import discord
from discord.ext import commands
from sentry_sdk import capture_exception

from app.features.issues import ISSUE_REGEX, handle_issues
from app.setup import bot, config


@bot.event
async def on_ready() -> None:
    print(f"Bot logged on as {bot.user}!")


@bot.event
async def on_error(*_: object) -> None:
    handle_error(cast(BaseException, sys.exc_info()[1]))


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction, error: Exception
) -> None:
    await interaction.response.send_message("Something went wrong :(", ephemeral=True)
    handle_error(error)


@bot.event
async def on_message(message: discord.Message) -> None:
    # Ignore our own messages
    if message.author == bot.user:
        return

    # Special trigger command to request an invite.
    # trigger = "I WANT GHOSTTY"
    # if message.content.strip().upper() == trigger:
    #     if message.guild is None:
    #         await message.channel.send("Tell me you want me in the Ghostty server!")
    #         return
    #
    #     if message.content.strip() == trigger:
    #         # TODO
    #         return
    #
    #     await message.channel.send("Louder. LOUDER!!")
    #     return

    # Simple test
    if message.guild is None and message.content == "ping":
        await message.author.send("pong")
        return

    # Look for issue numbers and link them
    if ISSUE_REGEX.search(message.content):
        await handle_issues(message)

    # Delete non-image messages in #showcase
    if message.channel.id == config.SHOWCASE_CHANNEL_ID and not message.attachments:
        await message.delete()

    # Owner-only sync command
    if message.content.rstrip() == "!sync":
        await sync(bot, message)


async def sync(bot: commands.Bot, message: discord.Message) -> None:
    """Syncs all global commands."""
    if not await bot.is_owner(message.author):
        return
    await bot.tree.sync()
    await message.author.send("Command tree synced.")


def handle_error(error: BaseException) -> None:
    if _is_ratelimit(error):
        # Restart the bot with a delay at startup.
        # This effectively replaces the current process.
        os.execv(
            sys.executable,
            (
                "python",
                Path(__file__).parent / "__main__.py",
                *sys.argv[1:],
                "--rate-limit-delay",
            ),
        )
    capture_exception(error)


def _is_ratelimit(error: BaseException) -> bool:
    if isinstance(error, discord.app_commands.CommandInvokeError):
        error = error.original
    return isinstance(error, discord.HTTPException) and error.status == 429

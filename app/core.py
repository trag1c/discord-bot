import discord
from discord.ext import commands

from app.features.issues import ISSUE_REGEX, handle_issues
from app.setup import bot, config


@bot.event
async def on_ready() -> None:
    print(f"Bot logged on as {bot.user}!")


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

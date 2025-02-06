import re
from types import SimpleNamespace
from typing import cast

import discord

from app.components.entity_mentions import entity_message
from app.setup import bot, config
from app.utils import is_dm, is_helper, is_mod

TAG_PATTERN = re.compile(r"\[(?:SOLVED|MOVED: #\d+)\]", re.IGNORECASE)


@bot.tree.command(name="close", description="Mark current post as resolved.")
@discord.app_commands.describe(
    gh_number="GitHub entity number for #help posts moved there"
)
@discord.app_commands.guild_only()
async def close_post(
    interaction: discord.Interaction, gh_number: int | None = None
) -> None:
    if not (
        isinstance(post := interaction.channel, discord.Thread)
        and post.parent_id == config.HELP_CHANNEL_ID
    ):
        await interaction.response.send_message(
            f"This command can only be used in <#{config.HELP_CHANNEL_ID}> posts.",
            ephemeral=True,
        )
        return

    assert not is_dm(interaction.user)
    if not (
        is_mod(interaction.user)
        or is_helper(interaction.user)
        or interaction.user.id == post.owner_id
    ):
        await interaction.response.send_message(
            "You don't have permission to close this post.", ephemeral=True
        )
        return

    if post.archived:
        await interaction.response.send_message(
            "This post is already closed.", ephemeral=True
        )
        return

    help_tags = cast(discord.ForumChannel, post.parent).available_tags
    desired_tag_id = config.HELP_CHANNEL_TAG_IDS["github" if gh_number else "solved"]
    tag = next(tag for tag in help_tags if tag.id == desired_tag_id)
    await post.add_tags(tag)

    await interaction.response.defer(ephemeral=True)

    if not TAG_PATTERN.search(post.name):
        post_name_tag = f"[MOVED: #{gh_number}]" if gh_number else "[SOLVED]"
        await post.edit(name=f"{post_name_tag} {post.name}")

    if gh_number:
        # Pretending this is a message to use the entity_mentions logic
        message = cast(
            discord.Message,
            SimpleNamespace(
                content=f"#{gh_number}",
                author=SimpleNamespace(id=interaction.user.id),
            ),
        )
        msg_content, _ = await entity_message(message)
        await post.send(msg_content)

    await post.edit(archived=True)
    await interaction.followup.send("Post marked as resolved.", ephemeral=True)

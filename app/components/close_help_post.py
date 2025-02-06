from types import SimpleNamespace
from typing import Literal, cast

import discord
from discord import app_commands

from app.components.docs import get_docs_link
from app.components.entity_mentions import entity_message
from app.setup import bot, config
from app.utils import is_dm, is_helper, is_mod


async def mention_entity(entity_id: int, owner_id: int) -> str:
    msg, _ = await entity_message(
        # Forging a message to use the entity_mentions logic
        cast(
            discord.Message,
            SimpleNamespace(
                content=f"#{entity_id}",
                author=SimpleNamespace(id=owner_id),
            ),
        )
    )
    return msg


class Close(app_commands.Group):
    @app_commands.command(name="solved", description="Mark post as solved.")
    @app_commands.describe(config_option="Config option name (optional)")
    async def solved(
        self, interaction: discord.Interaction, config_option: str | None = None
    ) -> None:
        if config_option:
            additional_reply = get_docs_link("option", config_option)
            title_prefix = f"[SOLVED: {config_option}]"
        else:
            title_prefix = additional_reply = None
        await close_post(interaction, "solved", title_prefix, additional_reply)

    @app_commands.command(name="moved", description="Mark post as moved to GitHub.")
    @app_commands.describe(entity_id="New GitHub entity number")
    async def moved(self, interaction: discord.Interaction, entity_id: int) -> None:
        await close_post(
            interaction,
            "moved",
            title_prefix=f"[MOVED: #{entity_id}]",
            additional_reply=await mention_entity(entity_id, interaction.user.id),
        )

    @app_commands.command(name="duplicate", description="Mark post as duplicate.")
    @app_commands.describe(
        original="The original GitHub entity (number) or help post (ID or link)"
    )
    async def duplicate(self, interaction: discord.Interaction, original: str) -> None:
        *_, id_ = original.rpartition("/")
        if len(id_) < 10:
            # GitHub entity number
            title_prefix = f"[DUPLICATE: #{id_}]"
            additional_reply = await mention_entity(int(id_), interaction.user.id)
        else:
            # Help post ID
            title_prefix = None
            additional_reply = f"Original post: <#{id_}>"
        await close_post(interaction, "duplicate", title_prefix, additional_reply)

    @app_commands.command(name="stale", description="Mark post as stale.")
    async def stale(self, interaction: discord.Interaction) -> None:
        await close_post(interaction, "stale")

    @app_commands.command(name="wontfix", description="Mark post as stale.")
    async def wontfix(self, interaction: discord.Interaction) -> None:
        await close_post(interaction, "stale", "[WON'T FIX]")


bot.tree.add_command(Close(name="close", description="Mark current post as resolved."))


async def close_post(
    interaction: discord.Interaction,
    tag: Literal["solved", "moved", "duplicate", "stale"],
    title_prefix: str | None = None,
    additional_reply: str | None = None,
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

    user = interaction.user
    assert not is_dm(user)
    if not (is_mod(user) or is_helper(user) or user.id == post.owner_id):
        await interaction.response.send_message(
            "You don't have permission to resolve this post.", ephemeral=True
        )
        return

    help_tags = {tag for tag in cast(discord.ForumChannel, post.parent).available_tags}

    if set(post.applied_tags) & help_tags:
        await interaction.response.send_message(
            "This post was already resolved.", ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True)

    desired_tag_id = config.HELP_CHANNEL_TAG_IDS[tag]
    await post.add_tags(next(tag for tag in help_tags if tag.id == desired_tag_id))

    if title_prefix is None:
        title_prefix = f"[{tag.upper()}]"
    await post.edit(name=f"{title_prefix} {post.name}")

    if additional_reply:
        await post.send(additional_reply)

    await interaction.followup.send("Post resolved.", ephemeral=True)

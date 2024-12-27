import asyncio
import re
from contextlib import suppress
from types import SimpleNamespace

import discord
import github
from discord import Message
from github.Repository import Repository

from app.setup import config, gh
from app.utils import is_dm, try_dm
from app.view import DeleteMention

ENTITY_REGEX = re.compile(r"#(\d{1,6})(?!\.\d)\b")
ENTITY_TEMPLATE = "**{kind} #{entity.number}:** {entity.title}\n<{entity.html_url}>\n"
IGNORED_MESSAGE_TYPES = frozenset(
    (discord.MessageType.thread_created, discord.MessageType.channel_name_change)
)

DISCUSSION_QUERY = """
query getDiscussion($number: Int!, $org: String!, $repo: String!) {
  repository(owner: $org, name: $repo) {
    discussion(number: $number) {
      title
      number
      html_url: url
    }
  }
}
"""


async def handle_entities(message: Message) -> None:
    if message.author.bot or message.type in IGNORED_MESSAGE_TYPES:
        return

    if is_dm(message.author):
        await try_dm(
            message.author,
            "You can only mention entities in the Ghostty server.",
        )
        return

    repo = gh.get_repo(f"{config.GITHUB_ORG}/{config.GITHUB_REPO}", lazy=True)

    entities: list[str] = []
    for match in ENTITY_REGEX.finditer(message.content):
        entity_id = int(match[1])
        try:
            entity = repo.get_issue(entity_id)
            kind = "Pull Request" if entity.pull_request else "Issue"
        except github.UnknownObjectException:
            try:
                entity = get_discussion(repo, entity_id)
                kind = "Discussion"
            except github.GithubException:
                continue
        if entity_id < 10:
            # Ignore single-digit mentions (likely a false positive)
            continue
        entities.append(ENTITY_TEMPLATE.format(kind=kind, entity=entity))

    if not entities:
        return

    sent_message = await message.reply(
        "\n".join(dict.fromkeys(entities)),
        mention_author=False,
        view=DeleteMention(message, len(entities)),
    )
    await asyncio.sleep(30)
    with suppress(discord.NotFound):
        await sent_message.edit(view=None)


def get_discussion(repo: Repository, number: int) -> SimpleNamespace:
    _, response = repo._requester.graphql_query(
        query=DISCUSSION_QUERY,
        variables={
            "number": number,
            "org": config.GITHUB_ORG,
            "repo": config.GITHUB_REPO,
        },
    )
    data = response["data"]["repository"]["discussion"]
    return SimpleNamespace(**data)

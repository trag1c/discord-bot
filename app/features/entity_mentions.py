import asyncio
import datetime as dt
import re
from contextlib import suppress
from types import SimpleNamespace
from typing import Literal, Protocol, cast

import discord
import github
from discord import Message
from github.Repository import Repository

from app.setup import bot, config, gh
from app.utils import is_dm, try_dm
from app.view import DeleteMention

ENTITY_REGEX = re.compile(r"(?:\b(web|bot|main))?#(\d{1,6})(?!\.\d)\b")
ENTITY_TEMPLATE = "**{kind} #{entity.number}:** {entity.title}\n<{entity.html_url}>\n"
IGNORED_MESSAGE_TYPES = frozenset(
    (discord.MessageType.thread_created, discord.MessageType.channel_name_change)
)
REPOSITORIES: dict[str, Repository] = {
    kind: gh.get_repo(f"{config.GITHUB_ORG}/{name}", lazy=True)
    for kind, name in config.GITHUB_REPOS.items()
}

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

RepoName = Literal["web", "bot", "main"]
CacheKey = tuple[RepoName, int]
EntityKind = Literal["Pull Request", "Issue", "Discussion"]


class Entity(Protocol):
    number: int
    title: str
    html_url: str


class TTLCache:
    def __init__(self, ttl: int) -> None:
        self._ttl = dt.timedelta(seconds=ttl)
        self._cache: dict[CacheKey, tuple[dt.datetime, EntityKind, Entity]] = {}

    def _fetch_entity(self, key: CacheKey) -> None:
        repo_name, entity_id = key
        try:
            entity = REPOSITORIES[repo_name].get_issue(entity_id)
            kind = "Pull Request" if entity.pull_request else "Issue"
        except github.UnknownObjectException:
            try:
                entity = get_discussion(REPOSITORIES[repo_name], entity_id)
                kind = "Discussion"
            except github.GithubException:
                raise KeyError(key) from None
        self._cache[key] = (dt.datetime.now(), kind, cast(Entity, entity))

    def _refresh(self, key: CacheKey) -> None:
        if key not in self._cache:
            self._fetch_entity(key)
            return
        timestamp, *_ = self._cache[key]
        if dt.datetime.now() - timestamp >= self._ttl:
            self._fetch_entity(key)

    def __getitem__(self, key: CacheKey) -> tuple[EntityKind, Entity]:
        self._refresh(key)
        _, kind, entity = self._cache[key]
        return kind, entity


entity_cache = TTLCache(1800)  # 30 minutes

message_to_mentions: dict[discord.Message, discord.Message] = {}


def _get_entities(message: discord.Message) -> tuple[str, int]:
    entities: list[str] = []
    for match in ENTITY_REGEX.finditer(message.content):
        repo_name = cast(RepoName, match[1] or "main")
        kind, entity = entity_cache[repo_name, int(match[2])]
        if entity.number < 10:
            # Ignore single-digit mentions (likely a false positive)
            continue
        entities.append(ENTITY_TEMPLATE.format(kind=kind, entity=entity))
    return "\n".join(dict.fromkeys(entities)), len(entities)


async def remove_button_after_timeout(message: discord.Message) -> None:
    await asyncio.sleep(30)
    with suppress(discord.NotFound, discord.HTTPException):
        await message.edit(view=None)


async def handle_entities(message: Message) -> None:
    if message.author.bot or message.type in IGNORED_MESSAGE_TYPES:
        return

    if is_dm(message.author):
        await try_dm(
            message.author,
            "You can only mention entities in the Ghostty server.",
        )
        return

    msg_content, entity_count = _get_entities(message)

    if not msg_content:
        return

    sent_message = await message.reply(
        msg_content, mention_author=False, view=DeleteMention(message, entity_count)
    )
    message_to_mentions[message] = sent_message
    await remove_button_after_timeout(sent_message)


def get_discussion(repo: Repository, number: int) -> SimpleNamespace:
    _, response = repo._requester.graphql_query(
        query=DISCUSSION_QUERY,
        variables={
            "number": number,
            "org": config.GITHUB_ORG,
            "repo": repo.name,
        },
    )
    data = response["data"]["repository"]["discussion"]
    return SimpleNamespace(**data)


@bot.event
async def on_message_delete(message: discord.Message) -> None:
    if (reply := message_to_mentions.get(message)) is not None:
        await reply.delete()
        del message_to_mentions[message]


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message) -> None:
    if before.content == after.content:
        return
    if _get_entities(before) == (new_entities := _get_entities(after)):
        return

    if (reply := message_to_mentions.get(before)) is not None:
        content, count = new_entities
        await reply.edit(
            content=content,
            view=DeleteMention(after, count),
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await remove_button_after_timeout(reply)

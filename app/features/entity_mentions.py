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

from app.setup import config, gh
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


async def handle_entities(message: Message) -> None:
    if message.author.bot or message.type in IGNORED_MESSAGE_TYPES:
        return

    if is_dm(message.author):
        await try_dm(
            message.author,
            "You can only mention entities in the Ghostty server.",
        )
        return

    entities: list[str] = []
    for match in ENTITY_REGEX.finditer(message.content):
        repo_name = cast(RepoName, match[1] or "main")
        kind, entity = entity_cache[repo_name, int(match[2])]
        if entity.number < 10:
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
            "repo": repo.name,
        },
    )
    data = response["data"]["repository"]["discussion"]
    return SimpleNamespace(**data)

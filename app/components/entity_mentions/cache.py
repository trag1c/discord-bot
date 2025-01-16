import datetime as dt
from typing import Literal, Protocol, cast

from githubkit.exception import RequestFailed

from app.setup import config, gh

from .discussions import get_discussion

type RepoName = Literal["web", "bot", "main"]
type CacheKey = tuple[RepoName, int]
type EntityKind = Literal["Pull Request", "Issue", "Discussion"]


class GitHubUser(Protocol):
    login: str


class Entity(Protocol):
    number: int
    title: str
    html_url: str
    user: GitHubUser
    created_at: dt.datetime


class TTRCache:
    def __init__(self, ttr: int) -> None:
        self._ttr = dt.timedelta(seconds=ttr)
        self._cache: dict[CacheKey, tuple[dt.datetime, EntityKind, Entity]] = {}

    async def _fetch_entity(self, key: CacheKey) -> None:
        repo_name, entity_id = key
        repo_path = (config.GITHUB_ORG, config.GITHUB_REPOS[repo_name])
        try:
            entity = (await gh.rest.issues.async_get(*repo_path, entity_id)).parsed_data
            kind = "Issue"
            if entity.pull_request:
                entity = (
                    await gh.rest.pulls.async_get(*repo_path, entity_id)
                ).parsed_data
                kind = "Pull Request"
        except RequestFailed:
            entity = await get_discussion(*repo_path, entity_id)
            kind = "Discussion"
        self._cache[key] = (dt.datetime.now(), kind, cast(Entity, entity))

    async def _refresh(self, key: CacheKey) -> None:
        if key not in self._cache:
            await self._fetch_entity(key)
            return
        timestamp, *_ = self._cache[key]
        if dt.datetime.now() - timestamp >= self._ttr:
            await self._fetch_entity(key)

    async def get(self, repo: RepoName, number: int) -> tuple[EntityKind, Entity]:
        key = repo, number
        await self._refresh(key)
        _, kind, entity = self._cache[key]
        return kind, entity


entity_cache = TTRCache(1800)  # 30 minutes

import re
from types import SimpleNamespace

import github
from discord import Message
from github.Repository import Repository

from app.setup import config, gh
from app.utils import is_dm, is_tester, try_dm

REPO_URL = "https://github.com/ghostty-org/ghostty/"
ENTITY_REGEX = re.compile(
    rf"({REPO_URL}(?:issues|pull|discussions)/|#)(\d{{2,6}})(?!\.\d)\b"
)
ENTITY_TEMPLATE = "**{kind} #{entity.number}:** {entity.title}\n"

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
    if message.author.bot:
        return

    if is_dm(message.author):
        await try_dm(
            message.author,
            "You can only mention entities in the Ghostty server.",
        )
        return

    if not is_tester(message.author):
        return

    repo = gh.get_repo(
        f"{config.GITHUB_ORG}/{config.GITHUB_REPO}",
        lazy=True,
    )

    entities = set()
    for match in ENTITY_REGEX.finditer(message.content):
        id_ = int(match[2])
        try:
            entity = repo.get_issue(id_)
            kind = "Pull Request" if entity.pull_request else "Issue"
        except github.UnknownObjectException:
            try:
                entity = get_discussion(repo, id_)
                kind = "Discussion"
            except github.GithubException:
                continue
        entity_info = ENTITY_TEMPLATE.format(kind=kind, entity=entity)
        entities.add(
            # Include a URL if the entity is mentioned by number
            f"{entity_info}{entity.html_url}\n" if match[1] == "#" else entity_info
        )

    if not entities:
        return

    await message.reply("\n".join(entities), mention_author=False)


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

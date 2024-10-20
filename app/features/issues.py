import re
from types import SimpleNamespace

import github
from discord import Message
from github.Repository import Repository

from app.setup import config, gh
from app.utils import is_dm, is_tester, try_dm

ISSUE_REGEX = re.compile(r"#(\d{2,6})(?!\.\d)\b")
ISSUE_TEMPLATE = "**{kind} #{issue.number}:** {issue.title}\n{issue.html_url}\n"

DISCUSSION_QUERY = """
query getDiscussion($number: Int!, $org: String!, $repo: String!) {
  repository(owner: $org, name: $repo) {
    discussion(number: $number) {
      title
      html_url: url
    }
  }
}
""".strip()


async def handle_issues(message: Message) -> None:
    if message.author.bot:
        return

    if is_dm(message.author):
        await try_dm(
            message.author,
            "You can only mention issues/PRs in the Ghostty server.",
        )
        return

    if not is_tester(message.author):
        return

    repo = gh.get_repo(
        f"{config.GITHUB_ORG}/{config.GITHUB_REPO}",
        lazy=True,
    )

    issues = set()
    for match in ISSUE_REGEX.finditer(message.content):
        id_ = int(match[1])
        try:
            issue = repo.get_issue(id_)
            kind = "Pull Request" if issue.pull_request else "Issue"
        except github.UnknownObjectException:
            try:
                issue = get_discussion(repo, id_)
                kind = "Discussion"
            except github.GithubException:
                continue
        issues.add(ISSUE_TEMPLATE.format(kind=kind, issue=issue))

    if not issues:
        return

    await message.reply("\n".join(issues), mention_author=False)


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
    return SimpleNamespace(**data, number=number)

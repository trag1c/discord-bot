import re

import github
from discord import Message

from app.setup import config, gh
from app.utils import is_dm, is_tester

ISSUE_REGEX = re.compile(r"#(\d{2,})(?!\.\d)\b")
ISSUE_TEMPLATE = "**{kind} #{issue.number}:** {issue.title}\n{issue.html_url}\n"


async def handle_issues(message: Message) -> None:
    if message.author.bot:
        return

    if is_dm(message.author):
        await message.channel.send(
            "You can only mention issues/PRs in the Ghostty server."
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
        try:
            issue = repo.get_issue(int(match[1]))
        except github.UnknownObjectException:
            continue
        kind = "Pull Request" if issue.pull_request else "Issue"
        issues.add(ISSUE_TEMPLATE.format(kind=kind, issue=issue))

    if not issues:
        return

    await message.reply("\n".join(issues), mention_author=False)

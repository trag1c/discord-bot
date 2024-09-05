import re

import discord
import github
from discord import Message

from app import config
from app.github import g
from app.utils import is_tester

ISSUE_REGEX = re.compile(r"#(\d{2,})(?!\.\d)\b")
ISSUE_TEMPLATE = "**{kind} #{issue.number}:** {issue.title}\n{issue.html_url}\n"


async def handle_issues(message: Message) -> None:
    if not isinstance(message.author, discord.Member):
        await message.channel.send(
            "You can only mention issues/PRs in the Ghostty server."
        )
        return

    if not is_tester(message.author):
        return

    repo = g.get_repo(
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

import re

import discord
import github
from discord import Message

from app import config
from app.github import g

ISSUE_REGEX = re.compile(r"#(\d+)\b")
ISSUE_TEMPLATE = "**{kind} #{issue.number}:** {issue.title}\n{issue.html_url}\n"


async def handle_issues(message: Message) -> None:
    if not isinstance(message.author, discord.Member):
        await message.channel.send(
            "You can only mention issues/PRs in the Ghostty server."
        )
        return

    # Check if the user is a tester.
    if message.author.get_role(config.tester_role_id) is None:
        return

    repo = g.get_repo(
        f"{config.github_org}/{config.github_repo}",
        lazy=True,
    )

    issues = []
    for match in ISSUE_REGEX.finditer(message.content):
        try:
            issue = repo.get_issue(int(match[1]))
        except github.UnknownObjectException:
            continue
        kind = "Pull Request" if issue.pull_request else "Issue"
        issues.append(ISSUE_TEMPLATE.format(kind=kind, issue=issue))

    await message.reply("\n".join(issues), mention_author=False)

import re

import github
from discord import Message

from app import config
from app.github import g

ISSUE_REGEX = re.compile(r"#(\d+)")
ISSUE_TEMPLATE = "**{kind} #{issue.number}:** {issue.title}\n{issue.html_url}\n"


async def handle_issues(message: Message) -> None:
    if message.guild is None:
        await message.channel.send(
            "You can only mention issues/PRs in the Ghostty server."
        )
        return

    # Check if the user is a tester
    member = message.guild.get_member(message.author.id)
    if member is None or member.get_role(config.tester_role_id) is None:
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

import datetime as dt
from types import SimpleNamespace

from github.Repository import Repository

from app.setup import config

DISCUSSION_QUERY = """
query getDiscussion($number: Int!, $org: String!, $repo: String!) {
  repository(owner: $org, name: $repo) {
    discussion(number: $number) {
      title
      number
      user: author { login }
      created_at: createdAt
      html_url: url
      answered: isAnswered
    }
  }
}
"""


def get_discussion(repo: Repository, number: int) -> SimpleNamespace:
    _, response = repo._requester.requestJsonAndCheck(
        "POST",
        repo._requester.graphql_url,
        input={
            "query": DISCUSSION_QUERY,
            "variables": {
                "number": number,
                "org": config.GITHUB_ORG,
                "repo": repo.name,
            },
        },
    )
    if "errors" in response:
        raise KeyError((repo.name, number))
    data = response["data"]["repository"]["discussion"]
    return SimpleNamespace(
        user=SimpleNamespace(login=data.pop("user")["login"]),
        created_at=dt.datetime.fromisoformat(data.pop("created_at")),
        **data,
    )

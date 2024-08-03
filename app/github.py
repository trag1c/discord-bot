from github import Auth, Github

from app import config

g = Github(auth=Auth.Token(config.GITHUB_TOKEN))

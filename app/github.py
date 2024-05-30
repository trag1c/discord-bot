from github import Github, Auth

from . import config

g = Github(auth=Auth.Token(config.github_token))

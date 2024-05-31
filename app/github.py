from github import Github, Auth

from . import config

g = Github(auth=Auth.Token(config.github_token))
g_legacy = Github(auth=Auth.Token(config.github_legacy_token))

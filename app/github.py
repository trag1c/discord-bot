from github import Github, Auth

from . import config

github = Github(auth=Auth.Token(config.github_token))

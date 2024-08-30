import os

BOT_TOKEN = os.environ["BOT_TOKEN"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
GITHUB_ORG = os.environ["GITHUB_ORG"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
GITHUB_TESTER_TEAM = os.environ["GITHUB_TESTER_TEAM"]
GUILD_ID = int(os.environ["BOT_GUILD_ID"])
MOD_ROLE_ID = int(os.environ["BOT_MOD_ROLE_ID"])
GITHUB_ROLE_ID = int(os.environ["BOT_GITHUB_ROLE_ID"])
TESTER_ROLE_ID = int(os.environ["BOT_TESTER_ROLE_ID"])
SENTRY_DSN = os.getenv("SENTRY_DSN")
SHOWCASE_CHANNEL_ID = int(os.environ["BOT_SHOWCASE_CHANNEL_ID"])
MOD_CHANNEL_ID = int(os.environ["BOT_MOD_CHANNEL_ID"])

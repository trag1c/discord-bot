import os

import dotenv

dotenv.load_dotenv()

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
MEDIA_CHANNEL_ID = int(os.environ["BOT_MEDIA_CHANNEL_ID"])
SHOWCASE_CHANNEL_ID = int(os.environ["BOT_SHOWCASE_CHANNEL_ID"])
VOUCH_CHANNEL_ID = int(os.environ["BOT_VOUCH_CHANNEL_ID"])
INVITELOG_CHANNEL_ID = int(os.environ["BOT_INVITELOG_CHANNEL_ID"])
BOT_DATABASE_URL = os.environ["BOT_DATABASE_URL"]

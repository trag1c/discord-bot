import os

import dotenv

dotenv.load_dotenv()

BOT_TOKEN = os.environ["BOT_TOKEN"]

GITHUB_ORG = os.environ["GITHUB_ORG"]
GITHUB_REPO = os.environ["GITHUB_REPO"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]

SENTRY_DSN = os.getenv("SENTRY_DSN")

MEDIA_CHANNEL_ID = int(os.environ["BOT_MEDIA_CHANNEL_ID"])
MOD_ROLE_ID = int(os.environ["BOT_MOD_ROLE_ID"])
SHOWCASE_CHANNEL_ID = int(os.environ["BOT_SHOWCASE_CHANNEL_ID"])

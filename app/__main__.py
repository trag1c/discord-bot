import sentry_sdk

from app import config
from app.bot import bot

if config.sentry_dsn is not None:
    sentry_sdk.init(
        dsn=config.sentry_dsn,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

bot.run(config.bot_token)

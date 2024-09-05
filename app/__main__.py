import sentry_sdk

from app.core import bot, config

if config.SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

bot.run(config.BOT_TOKEN)

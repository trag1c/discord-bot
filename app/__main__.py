import sys
from time import sleep

import sentry_sdk

from app.core import bot, config, db

if config.SENTRY_DSN is not None:
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        traces_sample_rate=1.0,
        profiles_sample_rate=1.0,
    )

if "--rate-limit-delay" in sys.argv:
    print(
        "The bot went offline due to a rate limit."
        " It will come back online in 25 minutes."
    )
    sleep(60 * 25)

db.attempt_connect()
bot.run(config.BOT_TOKEN)

import os

bot_token = os.environ['BOT_TOKEN']
github_token = os.environ['GITHUB_TOKEN']
github_org = os.environ['GITHUB_ORG']
github_tester_team = os.environ['GITHUB_TESTER_TEAM']
guild_id = int(os.environ['BOT_GUILD_ID'])
mod_role_id = int(os.environ['BOT_MOD_ROLE_ID'])
github_role_id = int(os.environ['BOT_GITHUB_ROLE_ID'])
tester_role_id = int(os.environ['BOT_TESTER_ROLE_ID'])
sentry_dsn = os.environ.get('SENTRY_DSN')

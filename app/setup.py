import discord
from discord.ext import commands
from github import Auth, Github

from app import config

intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(
    command_prefix=commands.when_mentioned_or("!"),
    intents=intents,
    allowed_mentions=discord.AllowedMentions(everyone=False, roles=False),
)

gh = Github(auth=Auth.Token(config.GITHUB_TOKEN))

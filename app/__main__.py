import discord
from discord.ext import commands

from . import config
from .bot import bot

bot.run(config.bot_token)

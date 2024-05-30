import discord
from discord.ext import commands
from . import config, view

# Initialize our bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=intents)

@bot.event
async def on_ready():
    print(f'Bot logged on as {bot.user}!')


@bot.event
async def on_message(message):
    # Ignore our own messages
    if message.author == bot.user:
        return

    # Special trigger command to request an invite.
    # trigger = "I WANT GHOSTTY"
    # if message.content.strip().upper() == trigger:
    #     if message.guild is None:
    #         await message.channel.send("Tell me you want me in the Ghostty server!")
    #         return
    #
    #     if message.content.strip() == trigger:
    #         # TODO
    #         return
    #
    #     await message.channel.send("Louder. LOUDER!!")
    #     return

    # Unknow message, try commands
    await bot.process_commands(message)


@bot.command()
async def github(ctx: commands.Context):
    # Only allow this command in a guild
    if ctx.guild is None:
        await ctx.author.send("Send the command in the Ghostty server.")
        return

    # Verify the author is a tester
    if ctx.author.get_role(config.tester_role_id) is None:
        await ctx.author.send("You must be a tester to link your GitHub account.")
        return

    # Send the tester link view
    await ctx.author.send(new_tester_message, view=view.TesterWelcome())


@bot.command(name='add-tester')
async def add_tester(ctx: commands.Context):
    # Only allow this command in a guild
    if ctx.guild is None:
        return

    if ctx.author.get_role(config.mod_role_id) is None:
        await ctx.author.send("You need to be a mod to add testers.")
        return

    # For each mentioned user, we want to add the tester role. After
    # adding the tester role we also DM them instructions on how to
    # continue setting up their account.
    count = 0
    for user in ctx.message.mentions:
        if user == bot.user:
            continue

        await user.add_roles(
            discord.Object(config.tester_role_id),
            reason="add-tester command",
        )

        await user.send(new_tester_message, view=view.TesterWelcome())

        count += 1

    await ctx.author.send(f"Added {count} testers.")

new_tester_message = """
Hello! You've been invited to help test Ghostty. Thank you. Please press the
button below to provide your GitHub username. This will allow us to invite
you to the GitHub organization and give you access to the repository.

If the command below fails or you forget to complete this step, you can
always trigger this message again by sending a DM to this bot with the
message "!github".
""".strip()

import traceback

import discord
import github

from .. import config
from ..github import g, g_legacy

class TesterWelcome(discord.ui.View):
    """The view shown to new testers."""

    @discord.ui.button(label='Accept and Link GitHub')
    async def link(self, interaction: discord.Interaction, button: discord.ui.Button):
        #await interaction.response.send_modal(TesterLink())
        await interaction.response.send_modal(TesterLinkLegacy())


class TesterLink(discord.ui.Modal, title='Link GitHub'):
    """The modal shown to link a GitHub account."""

    username = discord.ui.TextInput(
        label='GitHub Username',
        placeholder='mitchellh',
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Defer since we're going to do a bunch of slow stuff.
        await interaction.response.defer(ephemeral=True, thinking=True)

        # If the user already has the github role it means they already linked.
        if interaction.user.get_role(config.github_role_id) is not None:
            await interaction.followup.send(tester_link_already, ephemeral=True)
            return

        # Get and verify the GitHub user
        try:
            user = g.get_user(self.username.value)
        except github.GithubException.UnknownObjectException:
            await interaction.followup.send(f"GitHub user '{self.username.value}' not found.", ephemeral=True)
            return

        # If the user is already a member of the org, they're already linked.
        try:
            user.get_organization_membership(config.github_org)
            await interaction.followup.send('You are already a member of the Ghostty GitHub organization.', ephemeral=True)
        except github.GithubException.UnknownObjectException:
            # This is good, they aren't a member yet.
            org = g.get_organization(config.github_org)
            team = org.get_team_by_slug(config.github_tester_team)
            org.invite_user(user=user, role='direct_member', teams=[team])

        # Add the github role. We do this even if the user was already
        # previously a member of the org so that they don't link another
        # account.
        await interaction.user.add_roles(
            discord.Object(config.github_role_id),
            reason="tester linked GitHub account",
        )

        await interaction.followup.send(tester_link_message, ephemeral=True)


    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)


class TesterLinkLegacy(discord.ui.Modal, title='Link GitHub'):
    """
    The modal shown to link a GitHub account.

    This is the legacy command that will add them to collaborators instead of
    the GitHub organization.
    """

    username = discord.ui.TextInput(
        label='GitHub Username',
        placeholder='mitchellh',
        required=True,
    )

    async def on_submit(self, interaction: discord.Interaction):
        # Defer since we're going to do a bunch of slow stuff.
        await interaction.response.defer(ephemeral=True, thinking=True)

        # If the user already has the github role it means they already linked.
        if interaction.user.get_role(config.github_role_id) is not None:
            await interaction.followup.send(tester_link_already, ephemeral=True)
            return

        # Get and verify the GitHub user
        try:
            user = g_legacy.get_user(self.username.value)
        except github.GithubException.UnknownObjectException:
            await interaction.followup.send(f"GitHub user '{self.username.value}' not found.", ephemeral=True)
            return

        # If the user is already a member of the org, they're already linked.
        repo = g_legacy.get_repo("mitchellh/ghostty")
        repo.add_to_collaborators(user)

        # Add the github role. We do this even if the user was already
        # previously a member of the org so that they don't link another
        # account.
        await interaction.user.add_roles(
            discord.Object(config.github_role_id),
            reason="tester linked GitHub account",
        )

        await interaction.followup.send(tester_link_message, ephemeral=True)


    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.followup.send('Oops! Something went wrong.', ephemeral=True)
        traceback.print_exception(type(error), error, error.__traceback__)


new_tester_dm = """
Hello! You've been invited to help test Ghostty. Thank you! To accept
the invite, please run the `/accept-invite` command in the Ghostty server.
"""

tester_accept_invite = """
Hello! You've been invited to help test Ghostty. Thank you. Please press the
button below to provide your GitHub username. This will allow us to invite
you to the GitHub organization and give you access to the repository.

If the command below fails or you forget to complete this step, you can
always trigger this message again by running the `/accept-invite` command.
""".strip()

tester_link_already = """
You've already linked a GitHub account. If you need to change it,
please contact a mod.
""".strip()

tester_link_message = """
Please read the README and the README_TESTERS.md file. Details on what to expect,
how to download/configure Ghostty, and a small FAQ are all present. You're an early
tester so I'm going to hold you to a higher bar and expect you'll read! Thanks. 🥰

I also just want to remind you that Ghostty is still early beta software, and
the goal of you joining is so that you can report what is lacking and help us
make Ghostty great for you (and maybe even contribute, if you want!). Most of us
in the community are able to use Ghostty all day every day for our full time jobs
and its working great, but every new person brings a new perspective and new workflow
and small "obvious" issues are common. Please report it and we'll make it better.

That being said, feel free to talk about Ghostty publicly. You're welcome to share
screenshots, stream with it, whatever. Just please do not share the source code yet.

You should have received an invite from GitHub with a link to the repo.

❤️ Mitchell
""".strip()

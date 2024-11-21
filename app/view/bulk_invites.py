import discord

from app import config, view
from app.features.invites import log_invite
from app.utils import Account, is_tester, try_dm


class ConfirmBulkInvite(discord.ui.View):
    def __init__(
        self, accounts: list[Account], message: discord.Message, prompt: str
    ) -> None:
        super().__init__(timeout=None)
        self._accounts = accounts
        self._message = message
        self._prompt = prompt
        self._used = False

    @discord.ui.button(
        label="Yes",
        emoji="✅",
        custom_id="ghostty:bulk_invite:confirm",
    )
    async def confirm(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        if self._used:
            return
        self._used = True
        await interaction.response.defer(thinking=True, ephemeral=True)

        invited = set[Account]()
        invalid = set[Account]()
        for account in self._accounts:
            if not isinstance(account, discord.Member):
                invalid.add(account)
                continue
            if is_tester(account):
                continue

            try:
                await account.add_roles(
                    discord.Object(config.TESTER_ROLE_ID),
                    reason="bulk invite",
                )
            except discord.errors.NotFound:
                continue

            await try_dm(account, view.NEW_TESTER_DM)
            await log_invite(
                interaction.user,
                account,
                note=f"bulk invite at {self._message.jump_url}",
            )
            invited.add(account)

        content = f"Invited {len(invited)} members."
        for kind, accounts in (
            ("already in beta", set(self._accounts) - invited - invalid),
            ("invalid", invalid),
        ):
            if n := len(accounts):
                content += f"\n{n} {'was' if n == 1 else 'were'} {kind}: "
                content += " ".join(acc.mention for acc in accounts)

        await interaction.followup.send(content=content, ephemeral=True)

    @discord.ui.button(
        label="No",
        emoji="❌",
        custom_id="ghostty:bulk_invite:cancel",
    )
    async def cancel(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        if self._used:
            return
        await interaction.response.edit_message(
            content="Bulk invite cancelled.", view=None
        )

import discord

from app import view
from app.db import models
from app.db.connect import Session
from app.setup import bot, config
from app.utils import try_dm


def register_vouch_view() -> None:
    bot.add_view(DecideVouch())


# This is the "view" which shows the accept/deny buttons
class DecideVouch(discord.ui.View):
    """
    Vouch is nullable so that we can recover on bot restarts.
    This is done with the interaction we have access to later.
    """

    def __init__(self, vouch: models.Vouch | None = None) -> None:
        super().__init__(timeout=None)
        self._vouch = vouch

    # Accept
    @discord.ui.button(
        label="Accept",
        emoji="✅",
        custom_id="ghostty:vouches:accept",
    )
    async def accept(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        self._populate_missing_vouch(interaction)
        assert self._vouch is not None
        guild = await bot.fetch_guild(config.GUILD_ID)
        member = await guild.fetch_member(self._vouch.receiver_id)

        with Session() as session:
            self._vouch.vouch_state = models.VouchState.ACCEPTED
            self._vouch.decider_id = interaction.user.id

            session.add(self._vouch)
            session.commit()

        content = (
            interaction.message.content + f"\n-# Accepted by {interaction.user.mention}"
        )

        await interaction.response.edit_message(content=content, view=None)
        await member.add_roles(
            discord.Object(config.TESTER_ROLE_ID),
            reason="accepted vouch",
        )

        from app.features.invites import log_invite  # avoiding a circular import

        await log_invite(
            interaction.user, member, note=f"vouched by <@{self._vouch.voucher_id}>"
        )

        await try_dm(member, view.NEW_TESTER_DM)

    # Deny
    @discord.ui.button(
        label="Deny",
        emoji="⛔",
        custom_id="ghostty:vouches:deny",
    )
    async def deny(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        self._populate_missing_vouch(interaction)
        await interaction.response.send_modal(RejectionModal(self._vouch))

    """
    Populates the vouch if it's not already populated.
    """

    def _populate_missing_vouch(self, interaction: discord.Interaction) -> None:
        if self._vouch is not None:
            return

        with Session() as session:
            self._vouch = (
                session.query(models.Vouch)
                .filter_by(interaction_id=interaction.message.id)
                .one()
            )


# Rejection Modal
class RejectionModal(discord.ui.Modal, title="Reject Vouch"):
    reason = discord.ui.TextInput(
        label="Reason for rejection:", style=discord.TextStyle.paragraph
    )

    def __init__(self, vouch: models.Vouch) -> None:
        super().__init__(timeout=None, custom_id="ghostty:vouches:rejectm")
        self._vouch = vouch

    async def on_submit(self, interaction: discord.Interaction) -> None:
        with Session() as session:
            self._vouch.vouch_state = models.VouchState.DENIED
            self._vouch.decider_id = interaction.user.id
            self._vouch.reason = self.reason.value

            session.add(self._vouch)
            session.commit()

        content = (
            interaction.message.content
            + f"\n-# Denied by {interaction.user.mention}"
            + f"\n-# Reason: {self.reason.value}"
        )

        await interaction.response.edit_message(content=content, view=None)

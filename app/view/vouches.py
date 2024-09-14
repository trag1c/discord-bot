import discord

from app import view
from app.db import models
from app.db.connect import Session
from app.setup import bot, config


class DecideVouch(discord.ui.View):
    def __init__(self, vouch: models.Vouch) -> None:
        super().__init__()
        self._vouch = vouch

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        guild = await bot.fetch_guild(config.GUILD_ID)
        member = await guild.fetch_member(self._vouch.receiver_id)
        await member.add_roles(
            discord.Object(config.TESTER_ROLE_ID),
            reason="accepted vouch",
        )
        await member.send(view.NEW_TESTER_DM)
        await self._handle_vouch_decision(interaction, models.VouchState.ACCEPTED)

    @discord.ui.button(label="Deny", style=discord.ButtonStyle.red)
    async def deny(
        self, interaction: discord.Interaction, but: discord.ui.Button
    ) -> None:
        await self._handle_vouch_decision(interaction, models.VouchState.DENIED)

    async def _handle_vouch_decision(
        self, interaction: discord.Interaction, decision: models.VouchState
    ) -> None:
        with Session() as session:
            self._vouch.vouch_state = decision
            self._vouch.decider_id = interaction.user.id

            session.add(self._vouch)
            session.commit()
        decision_str = decision.name.capitalize()
        content = (
            interaction.message.content
            + f"\n-# {decision_str} by {interaction.user.mention}"
        )
        await interaction.response.edit_message(content=content, view=None)

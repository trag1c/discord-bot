from datetime import datetime, timedelta

import discord

from app.db import models
from app.db.connect import transaction
from app.utils import is_tester


def get_user(user: discord.Member | int) -> models.User | None:
    """
    Fetches a user from the database.
    """
    lookup_id = user.id if isinstance(user, discord.Member) else user
    with transaction() as session:
        return (
            session.query(models.User)
            .filter(models.User.user_id == lookup_id)
            .one_or_none()
        )


def import_user(user: discord.Member) -> models.User:
    """
    Imports a user into the database.
    Because this is new, we just grandfather older users in with a valid
    set of cooldown times and a default of 0 vouches.
    """

    # We need a date from 1 week ago to use as a default
    since = datetime.now() - timedelta(weeks=1)

    with transaction() as session:
        db_user = models.User(
            user_id=user.id,
            tester_since=since if is_tester(user) else None,
            is_vouch_blacklisted=False,
        )

        session.add(db_user)
        session.commit()
        return user

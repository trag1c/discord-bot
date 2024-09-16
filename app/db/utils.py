import datetime as dt

import discord

from app.db import models
from app.db.connect import Session
from app.utils import is_tester


def fetch_user(user: discord.Member) -> models.User:
    if (db_user := get_user(user)) is None:
        db_user = import_user(user)
    return db_user


def get_user(user: discord.Member) -> models.User | None:
    """Fetches a user from the database."""
    with Session(expire_on_commit=False) as session:
        return (
            session.query(models.User)
            .filter(models.User.user_id == user.id)
            .one_or_none()
        )


def import_user(user: discord.Member, *, new_user: bool = False) -> models.User:
    """
    Imports a user into the database.
    Because this is new, we just grandfather older users in with a valid
    set of cooldown times and a default of 0 vouches.
    """

    # We need a date from 1 week ago to use as a default
    since = dt.datetime.now(tz=dt.UTC)
    if not new_user:
        since -= dt.timedelta(weeks=1)

    with Session(expire_on_commit=False) as session:
        db_user = models.User(
            user_id=user.id,
            tester_since=since if is_tester(user) else None,
            is_vouch_blacklisted=False,
        )

        session.add(db_user)
        session.commit()
        return db_user

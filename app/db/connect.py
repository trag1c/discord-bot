from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import text

from app import config

engine = create_engine(
    config.BOT_DATABASE_URL,
    pool_size=10,
    max_overflow=10,
    client_encoding="utf8",
)

Session = sessionmaker(bind=engine)


def attempt_connect() -> None:
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            print("Established connection to the database.")

    except Exception:
        engine.dispose()
        raise RuntimeError("Failed to connect to the database.")


def get_db_session():
    return Session()

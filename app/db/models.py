from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, BigInteger, DateTime, Boolean

Base = declarative_base()
metadata = Base.metadata

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, unique=True)
    tester_since = Column(DateTime, nullable=True)
    is_vouch_blacklisted = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<User id={self.id} user_id={self.user_id}>"


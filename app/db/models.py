from sqlalchemy import BigInteger, Boolean, Column, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base

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


class Vouch(Base):
    __tablename__ = "vouches"
    id = Column(Integer, primary_key=True)
    voucher_id = Column(BigInteger)
    receiver_id = Column(BigInteger)
    approver_id = Column(BigInteger, nullable=True)
    vouch_date = Column(DateTime, nullable=True)
    is_approved = Column(Boolean, default=False)

    def __repr__(self) -> str:
        return f"<Vouch id={self.id} voucher_id={self.voucher_id} receiver_id={self.receiver_id}>"

from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, DateTime, Text, Table, ForeignKey, Column
import datetime

class Base(DeclarativeBase):
    pass


UserTickerTable = Table(
    "user_ticker_subscriptions",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("ticker_id", Integer, ForeignKey("tickers.id", ondelete="CASCADE"), primary_key=True),
)

class TickerModel(Base):
    __tablename__ = 'tickers'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String, nullable=True)
    subscribers: Mapped[list['UserModel']] = relationship(
        'UserModel',
        secondary=UserTickerTable,
        back_populates='tickers'
    )


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    tickers: Mapped[list['TickerModel']] = relationship(
        'TickerModel',
        secondary=UserTickerTable,
        back_populates='subscribers'
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow
    )



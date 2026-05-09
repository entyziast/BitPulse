from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship
from sqlalchemy import Integer, String, DateTime, Text, Table, ForeignKey, Column, Enum, Float, Boolean, Numeric
import datetime
from schemas.alerts import AlertType, AlertOperator, AlertStatus


class Base(DeclarativeBase):
    pass


UserTickerTable = Table(
    "user_ticker_subscriptions",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("ticker_id", Integer, ForeignKey("tickers.id", ondelete="CASCADE"), primary_key=True),
)


class TickerPriceHistoryModel(Base):
    __tablename__ = 'ticker_price_history'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    ticker_id: Mapped[int] = mapped_column(ForeignKey('tickers.id', ondelete='CASCADE'), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(precision=20, scale=8), nullable=False)
    timestamp: Mapped[datetime.datetime] = mapped_column(DateTime, default=datetime.datetime.utcnow, index=True)


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
    alerts: Mapped[list["AlertModel"]] = relationship(back_populates="ticker")


class UserModel(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(16), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(Text, nullable=False)
    tg_chat_id: Mapped[int | None] = mapped_column(Integer, nullable=True, unique=True)
    tickers: Mapped[list['TickerModel']] = relationship(
        'TickerModel',
        secondary=UserTickerTable,
        back_populates='subscribers'
    )
    alerts: Mapped[list['AlertModel']] = relationship(back_populates="user")
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow
    )


class AlertModel(Base):
    __tablename__ = 'alerts'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True
    )
    ticker_id: Mapped[int] = mapped_column(
        ForeignKey("tickers.id", ondelete="CASCADE"),
        index=True
    )

    name: Mapped[str | None] = mapped_column(String(32), nullable=True)

    alert_type: Mapped[AlertType] = mapped_column(Enum(AlertType), nullable=False)
    alert_operator: Mapped[AlertOperator] = mapped_column(Enum(AlertOperator), nullable=False)
    target_value: Mapped[float] = mapped_column(Float, nullable=False)

    alert_status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.ACTIVE)

    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime, 
        default=datetime.datetime.utcnow,
        index=True,
    )
    triggered_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime, 
        nullable=True
    )

    user: Mapped["UserModel"] = relationship(back_populates="alerts")
    ticker: Mapped["TickerModel"] = relationship(back_populates="alerts")

    @property
    def symbol(self):
        return self.ticker.symbol if self.ticker else None
import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class PlotStatus(enum.StrEnum):
    WAITING_NOTICE = "waiting_notice"
    THIRD_PARTY_WINDOW = "third_party_window"
    AUCTION_TRACKED = "auction_tracked"
    COMPLETED = "completed"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    plots: Mapped[list["LandPlot"]] = relationship(back_populates="user")


class LandPlot(Base):
    __tablename__ = "land_plots"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    cadastral_number: Mapped[str | None] = mapped_column(String(64))
    region: Mapped[str] = mapped_column(String(128))
    municipality: Mapped[str] = mapped_column(String(128))
    submitted_at: Mapped[date] = mapped_column(Date)
    authority: Mapped[str | None] = mapped_column(String(256))
    address: Mapped[str | None] = mapped_column(String(256))
    comment: Mapped[str | None] = mapped_column(Text)
    status: Mapped[PlotStatus] = mapped_column(default=PlotStatus.WAITING_NOTICE)
    tracking_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped[User] = relationship(back_populates="plots")
    notice: Mapped["Notice | None"] = relationship(back_populates="plot", uselist=False)
    auction: Mapped["Auction | None"] = relationship(back_populates="plot", uselist=False)


class Notice(Base):
    __tablename__ = "notices"
    id: Mapped[int] = mapped_column(primary_key=True)
    plot_id: Mapped[int] = mapped_column(ForeignKey("land_plots.id"), unique=True)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    published_at: Mapped[date | None] = mapped_column(Date)
    deadline: Mapped[date] = mapped_column(Date)
    comment: Mapped[str | None] = mapped_column(Text)
    plot: Mapped[LandPlot] = relationship(back_populates="notice")


class Auction(Base):
    __tablename__ = "auctions"
    id: Mapped[int] = mapped_column(primary_key=True)
    plot_id: Mapped[int] = mapped_column(ForeignKey("land_plots.id"), unique=True)
    source_url: Mapped[str | None] = mapped_column(String(1024))
    application_deadline: Mapped[date | None] = mapped_column(Date)
    auction_date: Mapped[date | None] = mapped_column(Date)
    comment: Mapped[str | None] = mapped_column(Text)
    plot: Mapped[LandPlot] = relationship(back_populates="auction")


class SentReminder(Base):
    __tablename__ = "sent_reminders"
    __table_args__ = (UniqueConstraint("plot_id", "kind", "due_date", name="uq_reminder"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    plot_id: Mapped[int] = mapped_column(ForeignKey("land_plots.id"), index=True)
    kind: Mapped[str] = mapped_column(String(64))
    due_date: Mapped[date] = mapped_column(Date)
    sent_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

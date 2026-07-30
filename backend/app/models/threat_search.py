from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.database import Base


class ThreatSearch(Base):
    __tablename__ = "threat_searches"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    cve: Mapped[str] = mapped_column(
        String(50),
        index=True,
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    risk_level: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    cvss: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )

    epss_score: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )

    epss_percentile: Mapped[float] = mapped_column(
        Float,
        nullable=True,
    )

    known_exploited: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
    )

    product: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    searched_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )
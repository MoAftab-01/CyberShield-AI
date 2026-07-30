from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.database.database import Base


class URLScan(Base):
    __tablename__ = "url_scans"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    url = Column(String, nullable=False)

    domain = Column(String, nullable=False)

    uses_https = Column(Boolean, nullable=False)

    risk_score = Column(Integer, nullable=False)

    risk_level = Column(String(20), nullable=False)

    final_risk_score = Column(Integer, nullable=False)

    final_risk_level = Column(String(20), nullable=False)

    confidence = Column(Integer, nullable=False)

    is_safe = Column(Boolean, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
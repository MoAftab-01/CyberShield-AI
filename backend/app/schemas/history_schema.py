from datetime import datetime
from pydantic import BaseModel


class ThreatHistoryResponse(BaseModel):
    cve: str
    severity: str
    risk_level: str
    cvss: float | None = None
    epss_score: float | None = None
    known_exploited: bool
    product: str | None = None
    searched_at: datetime

    class Config:
        from_attributes = True
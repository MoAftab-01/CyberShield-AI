from datetime import datetime
from pydantic import BaseModel


class PasswordReport(BaseModel):
    id: int
    password_strength: str
    entropy: int
    score: int
    created_at: datetime

    class Config:
        from_attributes = True


class URLReport(BaseModel):
    id: int
    url: str
    domain: str
    uses_https: bool
    risk_score: int
    risk_level: str
    final_risk_score: int
    final_risk_level: str
    confidence: int
    is_safe: bool
    created_at: datetime

    class Config:
        from_attributes = True
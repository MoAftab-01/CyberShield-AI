from typing import List, Optional

from pydantic import BaseModel


class ThreatResponse(BaseModel):

    cve: str

    severity: str

    risk_level: str

    cvss: float

    exploitability_score: Optional[float] = None

    impact_score: Optional[float] = None

    published: str

    last_modified: str

    status: Optional[str] = None

    description: str

    weaknesses: List[str]

    references: List[str]

    known_exploited: bool

    due_date: Optional[str] = None

    required_action: Optional[str] = None

    vendor_project: Optional[str] = None

    product: Optional[str] = None

    ransomware_use: Optional[str] = None

    ai_summary: Optional[str] = None

    recommendations: List[str]

    epss_score: Optional[float] = None

    epss_percentile: Optional[float] = None

    epss_date: Optional[str] = None
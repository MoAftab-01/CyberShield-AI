from pydantic import BaseModel


class DashboardSummaryResponse(BaseModel):

    total_searches: int

    critical: int

    high: int

    medium: int

    low: int

    known_exploited: int

    average_cvss: float

    average_epss: float
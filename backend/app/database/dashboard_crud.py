from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.threat_search import ThreatSearch


class DashboardCRUD:

    @staticmethod
    def get_summary(db: Session):

        total_searches = db.query(ThreatSearch).count()

        critical = db.query(ThreatSearch).filter(
            ThreatSearch.severity == "CRITICAL"
        ).count()

        high = db.query(ThreatSearch).filter(
            ThreatSearch.severity == "HIGH"
        ).count()

        medium = db.query(ThreatSearch).filter(
            ThreatSearch.severity == "MEDIUM"
        ).count()

        low = db.query(ThreatSearch).filter(
            ThreatSearch.severity == "LOW"
        ).count()

        exploited = db.query(ThreatSearch).filter(
            ThreatSearch.known_exploited.is_(True)
        ).count()

        average_cvss = (
            db.query(func.avg(ThreatSearch.cvss)).scalar() or 0
        )

        average_epss = (
            db.query(func.avg(ThreatSearch.epss_score)).scalar() or 0
        )

        return {
            "total_searches": total_searches,
            "critical": critical,
            "high": high,
            "medium": medium,
            "low": low,
            "known_exploited": exploited,
            "average_cvss": round(average_cvss, 2),
            "average_epss": round(average_epss, 3),
        }
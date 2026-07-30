from sqlalchemy.orm import Session

from app.models.threat_search import ThreatSearch


class ThreatCRUD:

    @staticmethod
    def save_search(
        db: Session,
        data: dict,
    ) -> ThreatSearch:

        search = ThreatSearch(
            cve=data.get("cve"),
            severity=data.get("severity"),
            risk_level=data.get("risk_level"),
            cvss=data.get("cvss"),
            epss_score=data.get("epss_score"),
            epss_percentile=data.get("epss_percentile"),
            known_exploited=data.get("known_exploited"),
            product=data.get("product"),
        )

        db.add(search)
        db.commit()
        db.refresh(search)

        return search

    @staticmethod
    def get_recent_searches(
        db: Session,
        limit: int = 10,
    ):

        return (
            db.query(ThreatSearch)
            .order_by(ThreatSearch.searched_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_total_searches(db: Session) -> int:

        return db.query(ThreatSearch).count()

    
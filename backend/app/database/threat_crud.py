from sqlalchemy.orm import Session

from app.models.threat_search import ThreatSearch


class ThreatCRUD:

    @staticmethod
    def require_user_id(user_id: int) -> int:
        if type(user_id) is not int or user_id <= 0:
            raise ValueError("A valid authenticated user ID is required.")
        return user_id

    @staticmethod
    def save_search(
        db: Session,
        data: dict,
        *,
        user_id: int,
    ) -> ThreatSearch:

        search = ThreatSearch(
            user_id=ThreatCRUD.require_user_id(user_id),
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
        *,
        user_id: int,
        limit: int = 10,
    ):
        user_id = ThreatCRUD.require_user_id(user_id)

        return (
            db.query(ThreatSearch)
            .filter(ThreatSearch.user_id == user_id)
            .order_by(ThreatSearch.searched_at.desc())
            .limit(limit)
            .all()
        )

    @staticmethod
    def get_total_searches(db: Session, *, user_id: int) -> int:
        user_id = ThreatCRUD.require_user_id(user_id)

        return (
            db.query(ThreatSearch)
            .filter(ThreatSearch.user_id == user_id)
            .count()
        )

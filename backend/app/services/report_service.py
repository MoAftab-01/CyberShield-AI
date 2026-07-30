from sqlalchemy.orm import Session

from app.models.password_scan import PasswordScan
from app.models.url_scan import URLScan


class ReportService:

    @staticmethod
    def get_password_reports(
        db: Session,
        page: int,
        page_size: int,
    ):
        query = (
            db.query(PasswordScan)
            .order_by(PasswordScan.created_at.desc())
        )

        total = query.count()

        reports = (
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": reports,
        }

    @staticmethod
    def get_url_reports(
        db: Session,
        page: int,
        page_size: int,
    ):
        query = (
            db.query(URLScan)
            .order_by(URLScan.created_at.desc())
        )

        total = query.count()

        reports = (
            query
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "items": reports,
        }
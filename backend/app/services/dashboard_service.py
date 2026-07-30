from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.password_scan import PasswordScan
from app.models.url_scan import URLScan


class DashboardService:

    @staticmethod
    def get_dashboard_stats(db: Session):

        # -----------------------
        # Basic Counts
        # -----------------------
        password_count = db.query(PasswordScan).count()

        url_count = db.query(URLScan).count()

        threat_count = (
            db.query(URLScan)
            .filter(URLScan.is_safe == False)
            .count()
        )

        security_score = max(
            100 - (threat_count * 10),
            0,
        )

        # -----------------------
        # Password Distribution
        # -----------------------
        password_distribution = {
            "Weak": db.query(PasswordScan)
            .filter(PasswordScan.password_strength == "Weak")
            .count(),

            "Medium": db.query(PasswordScan)
            .filter(PasswordScan.password_strength == "Medium")
            .count(),

            "Strong": db.query(PasswordScan)
            .filter(PasswordScan.password_strength == "Strong")
            .count(),
        }

        # -----------------------
        # URL Distribution
        # -----------------------
        url_distribution = {
            "Low": db.query(URLScan)
            .filter(URLScan.final_risk_level == "Low")
            .count(),

            "Medium": db.query(URLScan)
            .filter(URLScan.final_risk_level == "Medium")
            .count(),

            "High": db.query(URLScan)
            .filter(URLScan.final_risk_level == "High")
            .count(),
        }

        # -----------------------
        # Top Domains
        # -----------------------
        top_domains = (
            db.query(
                URLScan.domain,
                func.count(URLScan.domain).label("count"),
            )
            .group_by(URLScan.domain)
            .order_by(func.count(URLScan.domain).desc())
            .limit(5)
            .all()
        )

        return {
            "stats": {
                "securityScore": security_score,
                "passwordsChecked": password_count,
                "urlsScanned": url_count,
                "threatsDetected": threat_count,
            },

            "passwordDistribution": password_distribution,

            "urlDistribution": url_distribution,

            "topDomains": [
                {
                    "domain": domain,
                    "count": count,
                }
                for domain, count in top_domains
            ],

            "activities": [
                {
                    "id": 1,
                    "title": "Dashboard generated successfully",
                    "time": "Just now",
                    "status": "success",
                }
            ],
        }
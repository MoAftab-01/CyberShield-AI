from sqlalchemy.orm import Session

from app.clients.cisa_client import CISAClient
from app.clients.nvd_client import NVDClient
from app.clients.epss_client import EPSSClient
from app.clients.github_client import GitHubClient

from app.mappers.threat_mapper import ThreatMapper
from app.mappers.epss_mapper import EPSSMapper
from app.mappers.github_mapper import GitHubMapper
from app.mappers.correlation_mapper import CorrelationMapper

from app.services.ai_service import AIService

from app.database.threat_crud import ThreatCRUD


class ThreatService:

    @staticmethod
    def get_cve(
        cve_id: str,
        db: Session,
    ):

        # ==========================
        # Collect Data
        # ==========================

        nvd = NVDClient.get_cve(cve_id)

        cisa = CISAClient.get_kev(cve_id)

        epss = EPSSClient.get_epss(cve_id)

        github = GitHubClient.get_advisory(cve_id)

        # ==========================
        # Normalize
        # ==========================

        result = ThreatMapper.normalize_nvd(nvd)

        result.update(cisa)

        result.update(
            EPSSMapper.normalize(epss)
        )

        result["github_advisories"] = (
            GitHubMapper.normalize(github)
        )

        # ==========================
        # MITRE (Temporary)
        # ==========================

        result["mitre_attack"] = []

        # ==========================
        # Threat Correlation
        # ==========================

        result.update(
            CorrelationMapper.correlate(result)
        )

        # ==========================
        # AI
        # ==========================

        result["ai_summary"] = (
            AIService.generate_summary(result)
        )

        result["recommendations"] = (
            AIService.generate_recommendations(result)
        )

        # ==========================
        # Save Search
        # ==========================

        ThreatCRUD.save_search(
            db=db,
            data=result,
        )

        return result

    @staticmethod
    def get_history(
        db: Session,
    ):
        return ThreatCRUD.get_recent_searches(db)

    @staticmethod
    def total_searches(
        db: Session,
    ):
        return ThreatCRUD.get_total_searches(db)
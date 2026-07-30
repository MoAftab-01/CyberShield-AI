from sqlalchemy.orm import Session

from app.clients.cisa_client import CISAClient
from app.clients.nvd_client import NVDClient
from app.clients.epss_client import EPSSClient

from app.mappers.threat_mapper import ThreatMapper
from app.mappers.epss_mapper import EPSSMapper

from app.services.ai_service import AIService

from app.database.threat_crud import ThreatCRUD


class ThreatService:

    @staticmethod
    def get_cve(
        cve_id: str,
        db: Session,
    ):

        # Collect data

        nvd = NVDClient.get_cve(cve_id)

        cisa = CISAClient.get_kev(cve_id)

        epss = EPSSClient.get_epss(cve_id)

        # Normalize NVD

        result = ThreatMapper.normalize_nvd(nvd)

        # Merge CISA

        result.update(cisa)

        # Merge EPSS

        result.update(
            EPSSMapper.normalize(epss)
        )

        # AI Summary

        result["ai_summary"] = (
            AIService.generate_summary(result)
        )

        # AI Recommendations

        result["recommendations"] = (
            AIService.generate_recommendations(result)
        )

        # Save Search

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
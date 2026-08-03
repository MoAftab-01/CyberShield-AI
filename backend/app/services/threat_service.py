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

from app.services.llm.provider_factory import ProviderFactory

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

    @staticmethod
    def explain(cve: str):

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                f"""
You are a cybersecurity expert.

Explain vulnerability {cve}.

Include:
- What it is
- Why it matters
- Business impact

Use markdown.
"""
            )
        }

    @staticmethod
    def remediation(cve: str):

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                f"""
You are a cybersecurity expert.

Provide remediation guidance for {cve}.

Use bullet points.

Focus on practical actions.
"""
            )
        }

    @staticmethod
    def mitre(cve: str):

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                f"""
Explain how {cve} relates to the MITRE ATT&CK framework.

Mention likely tactics and techniques.

Use markdown.
"""
            )
        }

    @staticmethod
    def summary(cve: str):

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                f"""
Provide an executive summary for {cve}.

Maximum 200 words.

Focus on business impact and urgency.
"""
            )
        }
from sqlalchemy.orm import Session

from app.database.models import User
from app.models.url_scan import URLScan
from app.integrations.virustotal import VirusTotalClient
from app.intelligence.threat_aggregator import ThreatAggregator
from app.schemas.url_schema import URLResponse
from app.utils.url_utils import (
    calculate_url_risk,
    contains_ip,
    count_subdomains,
    detect_keywords,
    extract_domain,
    is_valid_url,
    url_length,
    uses_https,
)

from app.services.llm.provider_factory import ProviderFactory

class URLService:

    @staticmethod
    async def analyze(
        db: Session,
        current_user: User,
        url: str,
    ) -> URLResponse:

        valid = is_valid_url(url)

        domain = extract_domain(url)

        https = uses_https(url)

        ip = contains_ip(url)

        length = url_length(url)

        keywords = detect_keywords(url)

        subdomains = count_subdomains(domain)

        score, level, recommendations = calculate_url_risk(
            https=https,
            contains_ip_address=ip,
            keywords=keywords,
            length=length,
            subdomains=subdomains,
        )

        vt = await VirusTotalClient.analyze_url(url)

        aggregation = ThreatAggregator.aggregate(
            local_score=score,
            vt_result=vt,
        )

        # -----------------------------
        # Save Scan
        # -----------------------------
        scan = URLScan(
            user_id=current_user.id,
            url=url,
            domain=domain,
            uses_https=https,
            risk_score=score,
            risk_level=level,
            final_risk_score=aggregation["final_score"],
            final_risk_level=aggregation["final_level"],
            confidence=aggregation["confidence"],
            is_safe=aggregation["final_level"].lower() == "low",
        )

        db.add(scan)
        db.commit()

        # -----------------------------
        # Return API Response
        # -----------------------------
        return URLResponse(
            url=url,
            is_valid_url=valid,
            uses_https=https,
            contains_ip_address=ip,
            domain=domain,
            url_length=length,
            suspicious_keywords=keywords,
            subdomain_count=subdomains,
            risk_score=score,
            risk_level=level,
            recommendations=recommendations,
            virustotal_found=vt["found"],
            virustotal_malicious=vt["malicious"],
            virustotal_suspicious=vt["suspicious"],
            virustotal_harmless=vt["harmless"],
            final_risk_score=aggregation["final_score"],
            final_risk_level=aggregation["final_level"],
            confidence=aggregation["confidence"],
            analysis_summary=aggregation["reasons"],
        )

    @staticmethod
    def explain(question: str):

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                f"""
You are a cybersecurity expert.

Explain the following URL security question.

Question:
{question}

Be concise and practical.
"""
            )
        }

    @staticmethod
    def recommend():

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                """
You are a cybersecurity expert.

Provide URL safety best practices.

Use markdown bullet points.

Maximum 8 bullets.
"""
            )
        }

    @staticmethod
    def education(question: str):

        provider = ProviderFactory.get_provider()

        return {
            "answer": provider.chat(
                f"""
You are a cybersecurity trainer.

Teach the following topic clearly.

Topic:
{question}

Use markdown headings and bullets.
"""
            )
        }    
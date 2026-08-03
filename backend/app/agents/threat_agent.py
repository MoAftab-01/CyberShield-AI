import re

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.agents.capability_router import CapabilityRouter

from app.services.threat_service import ThreatService


class ThreatAgent(BaseAgent):

    CAPABILITIES = [
        "lookup",
        "explain",
        "remediation",
        "mitre",
        "summary",
    ]

    def handle(
        self,
        question: str,
        db: Session,
        **kwargs,
    ):

        match = re.search(
            r"CVE-\d{4}-\d+",
            question,
            re.IGNORECASE,
        )

        if not match:

            return {
                "error": "No CVE ID found in the request."
            }

        cve = match.group(0).upper()

        capability = CapabilityRouter.route(
            agent="Threat Agent",
            capabilities=self.CAPABILITIES,
            question=question,
        )

        print(f"[ThreatAgent] {capability}")

        if capability == "explain":
            return ThreatService.explain(cve)

        elif capability == "remediation":
            return ThreatService.remediation(cve)

        elif capability == "mitre":
            return ThreatService.mitre(cve)

        elif capability == "summary":
            return ThreatService.summary(cve)

        return ThreatService.get_cve(
            cve_id=cve,
            db=db,
        )
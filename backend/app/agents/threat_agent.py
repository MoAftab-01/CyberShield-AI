import re

from sqlalchemy.orm import Session

from app.agents.base_agent import BaseAgent
from app.services.threat_service import ThreatService


class ThreatAgent(BaseAgent):

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

        return ThreatService.get_cve(
            cve_id=cve,
            db=db,
        )
"""Fixed-origin, read-only intelligence. Live mode requires operator opt-in.

Fixture mode never silently falls back to live HTTP. No model downloads.
"""
from datetime import date, timedelta
import json
import time

import requests
from app.agents.cve_input import validate_cve
from app.knowledge.registry import SourceRegistry

MAX_BYTES = 5_000_000


class OfflineIntelligence:
    fixture = True

    def lookup(self, source, cve):
        validate_cve(cve)
        if cve not in {"CVE-2021-44228", "CVE-2023-44487", "CVE-2024-3094"}:
            return ({"vulnerabilities": []} if source == "nvd" else
                    {"catalogVersion": "synthetic-demo-1", "dateReleased": date.today().isoformat(),
                     "vulnerabilities": []})
        if source == "nvd":
            # Explicit original synthetic fixture prose, not redistributed NVD text.
            descriptions = {
                "CVE-2021-44228": "Synthetic Log4Shell scenario: vulnerable logging components may allow remote code execution; confirm installed versions and exposure.",
                "CVE-2023-44487": "Synthetic HTTP/2 Rapid Reset scenario: affected servers may experience denial of service; confirm vendor guidance and deployed versions.",
                "CVE-2024-3094": "Synthetic XZ scenario: selected compromised releases require careful inventory and vendor review; actual asset impact is not established."}
            return {"vulnerabilities": [{"cve": {"id": cve, "published": "2024-04-01T00:00:00Z",
                "lastModified": "2024-04-02T00:00:00Z", "vulnStatus": "Analyzed",
                "descriptions": [{"lang": "en", "value": cve + ": " + descriptions[cve]}]}}]}
        if source != "cisa-kev":
            raise ValueError("Unknown source.")
        return {"catalogVersion": "synthetic-demo-1",
            "dateReleased": (date.today() - timedelta(days=1)).isoformat(),
            "vulnerabilities": [] if cve == "CVE-2024-3094" else [{
                "cveID": cve,
                "shortDescription": cve + " is listed in this synthetic KEV scenario.",
                "requiredAction": "Synthetic exercise: review official vendor mitigation guidance; no automatic action is authorized."}]}


class ReadOnlyLiveIntelligence:
    fixture = False

    def __init__(self, *, approved=False):
        if approved is not True:
            raise ValueError("Live intelligence requires explicit operator approval.")

    def lookup(self, source, cve):
        validate_cve(cve)
        if source not in {"nvd", "cisa-kev"}:
            raise ValueError("Unknown source.")
        definition = SourceRegistry().get(source)
        # Public fixed endpoints only. Never follow redirects or inherited proxy
        # credentials; never accept user-supplied URLs, headers or request methods.
        with requests.Session() as session:
            session.trust_env = False
            started = time.monotonic()
            try:
                with session.get(definition.machine_readable_url,
                    params={"cveId": cve} if source == "nvd" else None,
                    timeout=(3, 5), allow_redirects=False, stream=True,
                    headers={"Accept": "application/json", "User-Agent": "CyberShield-CVE-Investigator/1"}) as response:
                    if response.status_code == 429 or response.status_code >= 500:
                        raise TimeoutError("Source temporarily unavailable.")
                    if response.status_code != 200:
                        raise ValueError("Source request rejected.")
                    chunks, size = [], 0
                    for chunk in response.iter_content(65536):
                        size += len(chunk)
                        if size > MAX_BYTES or time.monotonic() - started > 10:
                            raise ValueError("Source response bound exceeded.")
                        chunks.append(chunk)
                    payload = json.loads(b"".join(chunks))
                    if not isinstance(payload, dict):
                        raise ValueError("Invalid source JSON.")
                    return payload
            except requests.RequestException:
                raise ConnectionError("Intelligence request unavailable.") from None

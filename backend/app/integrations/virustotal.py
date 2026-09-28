"""VirusTotal enrichment.

VirusTotal is a third-party dependency on a free-tier key with a low request
quota, so it is treated as optional enrichment rather than as a component the
scanner depends on. The original raised on any non-404 status, which meant a
rate limit (429), an expired key (401) or a VirusTotal outage turned a working
local URL analysis into a 500 for the user.

Every failure now returns a typed "unavailable" result instead. The local
heuristic still produces a verdict, and the caller can tell the user that
reputation data was not available - which is honest, and strictly better than
losing the analysis.
"""

import base64
import httpx

from app.core.config import settings

#: Kept short: this call is on the request path, and the frontend gives up at
#: 60s. A stalled third-party lookup must not consume that budget.
REQUEST_TIMEOUT_SECONDS = 8.0


class VirusTotalClient:
    BASE_URL = "https://www.virustotal.com/api/v3"

    @staticmethod
    def url_id(url: str) -> str:
        """
        VirusTotal identifies URLs using a URL-safe Base64 encoding
        with '=' padding removed.
        """
        encoded = base64.urlsafe_b64encode(
            url.encode()
        ).decode()

        return encoded.strip("=")

    @staticmethod
    async def analyze_url(url: str):
        """Look up a URL's reputation.

        Always returns a dict. ``available`` says whether VirusTotal answered;
        when it is False the counters are zero and ``reason`` explains why, so
        a caller can distinguish "clean" from "unknown" - a distinction the
        original conflated.
        """

        if not settings.VT_API_KEY:
            return VirusTotalClient._unavailable(
                "No VirusTotal API key is configured."
            )

        headers = {
            "x-apikey": settings.VT_API_KEY
        }

        url_id = VirusTotalClient.url_id(url)

        endpoint = f"{VirusTotalClient.BASE_URL}/urls/{url_id}"

        try:
            async with httpx.AsyncClient(
                timeout=REQUEST_TIMEOUT_SECONDS
            ) as client:

                response = await client.get(
                    endpoint,
                    headers=headers,
                )

        except httpx.HTTPError as error:
            return VirusTotalClient._unavailable(
                f"VirusTotal could not be reached ({type(error).__name__})."
            )

        if response.status_code == 404:
            # Not an error: VirusTotal has simply never seen this URL.
            return {
                "found": False,
                "available": True,
                "malicious": 0,
                "suspicious": 0,
                "harmless": 0,
            }

        if response.status_code == 429:
            return VirusTotalClient._unavailable(
                "VirusTotal rate limit reached for this API key."
            )

        if response.status_code in (401, 403):
            return VirusTotalClient._unavailable(
                "VirusTotal rejected the API key."
            )

        if response.status_code >= 400:
            return VirusTotalClient._unavailable(
                f"VirusTotal returned HTTP {response.status_code}."
            )

        try:
            data = response.json()
            stats = data["data"]["attributes"]["last_analysis_stats"]
        except (ValueError, KeyError, TypeError):
            return VirusTotalClient._unavailable(
                "VirusTotal returned a response in an unexpected shape."
            )

        return {
            "found": True,
            "available": True,
            "malicious": stats.get("malicious", 0),
            "suspicious": stats.get("suspicious", 0),
            "harmless": stats.get("harmless", 0),
        }

    @staticmethod
    def _unavailable(reason: str) -> dict:
        return {
            "found": False,
            "available": False,
            "malicious": 0,
            "suspicious": 0,
            "harmless": 0,
            "reason": reason,
        }

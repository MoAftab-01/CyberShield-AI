import base64
import httpx

from app.core.config import settings


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

        headers = {
            "x-apikey": settings.VT_API_KEY
        }

        url_id = VirusTotalClient.url_id(url)

        endpoint = f"{VirusTotalClient.BASE_URL}/urls/{url_id}"

        async with httpx.AsyncClient(timeout=15) as client:

            response = await client.get(
                endpoint,
                headers=headers,
            )

            if response.status_code == 404:

                return {
                    "found": False,
                    "malicious": 0,
                    "suspicious": 0,
                    "harmless": 0,
                }

            response.raise_for_status()

            data = response.json()

            stats = data["data"]["attributes"][
                "last_analysis_stats"
            ]

            return {
                "found": True,
                "malicious": stats.get("malicious", 0),
                "suspicious": stats.get("suspicious", 0),
                "harmless": stats.get("harmless", 0),
            }
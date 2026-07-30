import requests


class EPSSClient:
    """
    FIRST.org EPSS Client
    """

    BASE_URL = "https://api.first.org/data/v1/epss"

    @classmethod
    def get_epss(cls, cve_id: str):

        try:

            response = requests.get(
                cls.BASE_URL,
                params={"cve": cve_id},
                timeout=10,
            )

            response.raise_for_status()

            result = response.json()

            data = result.get("data", [])

            if not data:
                return None

            return data[0]

        except Exception as e:

            print(f"EPSS Error: {e}")

            return None
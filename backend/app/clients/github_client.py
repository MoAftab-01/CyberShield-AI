import requests


class GitHubClient:

    BASE_URL = "https://api.github.com/advisories"

    @classmethod
    def get_advisory(cls, cve_id: str):

        try:

            response = requests.get(
                cls.BASE_URL,
                params={
                    "cve_id": cve_id,
                },
                timeout=10,
            )

            if response.status_code != 200:
                return []

            return response.json()

        except Exception as e:

            print("GitHub Advisory Error:", e)

            return []
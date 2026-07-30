import requests

BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"


class NVDClient:
    @staticmethod
    def get_cve(cve_id: str):
        try:
            response = requests.get(
                BASE_URL,
                params={"cveId": cve_id},
                timeout=10,
            )

            response.raise_for_status()

            return response.json()

        except requests.exceptions.Timeout:
            raise Exception("NVD API request timed out.")

        except requests.exceptions.HTTPError as e:
            raise Exception(f"NVD API HTTP Error: {e}")

        except requests.exceptions.RequestException as e:
            raise Exception(f"NVD API Error: {e}")
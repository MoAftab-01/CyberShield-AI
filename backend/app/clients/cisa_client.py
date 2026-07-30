import requests

CISA_KEV_URL = (
    "https://www.cisa.gov/sites/default/files/feeds/"
    "known_exploited_vulnerabilities.json"
)


class CISAClient:

    @staticmethod
    def get_kev(cve_id: str):
        try:
            response = requests.get(CISA_KEV_URL, timeout=15)
            response.raise_for_status()

            data = response.json()

            for vuln in data.get("vulnerabilities", []):
                if vuln.get("cveID") == cve_id:
                    return {
                        "known_exploited": True,
                        "due_date": vuln.get("dueDate"),
                        "required_action": vuln.get("requiredAction"),
                        "vendor_project": vuln.get("vendorProject"),
                        "product": vuln.get("product"),
                        "ransomware_use": vuln.get("knownRansomwareCampaignUse"),
                    }

            return {
                "known_exploited": False,
                "due_date": None,
                "required_action": None,
                "vendor_project": None,
                "product": None,
                "ransomware_use": None,
            }

        except Exception as e:
            print(f"CISA Client Error: {e}")

            return {
                "known_exploited": False,
                "due_date": None,
                "required_action": None,
                "vendor_project": None,
                "product": None,
                "ransomware_use": None,
            }
from attackcti import attack_client


class MITREClient:
    """
    Client for retrieving MITRE ATT&CK information.
    """

    lift = attack_client()

    @classmethod
    def search_by_cve(cls, cve_id: str):
        """
        Returns ATT&CK techniques related to a CVE.
        """

        try:

            techniques = cls.lift.get_techniques()

            matches = []

            for tech in techniques:

                text = str(tech).lower()

                if cve_id.lower() in text:

                    matches.append(
                        {
                            "technique_id": tech.get(
                                "external_references",
                                [{}],
                            )[0].get("external_id"),

                            "name": tech.get("name"),

                            "description": tech.get("description"),

                            "tactic": tech.get(
                                "kill_chain_phases",
                                [{}],
                            )[0].get("phase_name"),
                        }
                    )

            return matches

        except Exception as e:

            print("MITRE Error:", e)

            return []
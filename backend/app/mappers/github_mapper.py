class GitHubMapper:

    @staticmethod
    def normalize(data):

        if not data:
            return []

        advisories = []

        for item in data:

            advisories.append(
                {
                    "ghsa_id": item.get("ghsa_id"),
                    "summary": item.get("summary"),
                    "severity": item.get("severity"),
                    "published_at": item.get("published_at"),
                    "updated_at": item.get("updated_at"),
                    "url": item.get("html_url"),
                }
            )

        return advisories
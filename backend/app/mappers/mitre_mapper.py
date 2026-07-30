class MitreMapper:

    @staticmethod
    def normalize(data):

        if not data:
            return []

        techniques = []

        for item in data:

            techniques.append(
                {
                    "technique_id": item.get("technique_id"),

                    "name": item.get("name"),

                    "description": item.get("description"),

                    "tactic": item.get("tactic"),
                }
            )

        return techniques
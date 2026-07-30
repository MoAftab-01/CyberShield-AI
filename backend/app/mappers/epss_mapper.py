class EPSSMapper:

    @staticmethod
    def normalize(data):

        if not data:
            return {
                "epss_score": None,
                "epss_percentile": None,
                "epss_date": None,
            }

        return {

            "epss_score": float(data.get("epss", 0)),

            "epss_percentile": float(data.get("percentile", 0)),

            "epss_date": data.get("date"),
        }
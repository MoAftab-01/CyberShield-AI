class AIService:

    @staticmethod
    def generate_summary(data: dict) -> str:

        severity = data.get("severity", "Unknown")

        exploited = data.get("known_exploited", False)

        epss = data.get("epss_score")

        risk = data.get("risk_level")

        summary = (
            f"This vulnerability has a {severity} severity "
            f"with an overall {risk} risk level."
        )

        if exploited:

            summary += (
                " It is present in the CISA Known Exploited "
                "Vulnerabilities catalog."
            )

        if epss is not None:

            summary += (
                f" EPSS predicts a "
                f"{epss * 100:.2f}% probability "
                f"of exploitation."
            )

        return summary

    @staticmethod
    def generate_recommendations(data: dict):

        recommendations = []

        if data.get("known_exploited"):

            recommendations.append(
                "Patch immediately because active exploitation has been observed."
            )

        if data.get("epss_score", 0) >= 0.70:

            recommendations.append(
                "Prioritize remediation due to high exploitation probability."
            )

        recommendations.extend(
            [
                "Apply the latest vendor patches.",
                "Monitor systems for indicators of compromise.",
                "Restrict unnecessary internet exposure.",
                "Review security logs for suspicious activity.",
            ]
        )

        return recommendations
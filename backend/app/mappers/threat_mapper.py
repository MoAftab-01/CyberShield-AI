from typing import Any, Dict


class ThreatMapper:

    @staticmethod
    def get_risk_level(score: float) -> str:

        if score >= 9.0:
            return "Critical"

        elif score >= 7.0:
            return "High"

        elif score >= 4.0:
            return "Medium"

        return "Low"

    @staticmethod
    def generate_ai_summary(
        severity: str,
        exploited: bool,
        epss: float | None,
    ) -> str:

        summary = (
            f"This vulnerability is classified as {severity}."
        )

        if exploited:

            summary += (
                " It is listed in CISA Known Exploited "
                "Vulnerabilities."
            )

        if epss is not None:

            summary += (
                f" EPSS predicts a "
                f"{epss * 100:.2f}% chance "
                f"of exploitation."
            )

        return summary

    @staticmethod
    def generate_recommendations(
        exploited: bool,
    ) -> list[str]:

        recommendations = [

            "Apply the latest vendor patches.",

            "Review affected systems.",

            "Monitor logs for exploitation attempts.",

            "Restrict unnecessary external exposure.",
        ]

        if exploited:

            recommendations.insert(
                0,
                "Prioritize immediate remediation because the vulnerability is actively exploited.",
            )

        return recommendations

    @staticmethod
    def normalize_nvd(
        data: Dict[str, Any],
    ) -> Dict[str, Any]:

        vulnerabilities = data.get(
            "vulnerabilities",
            [],
        )

        if not vulnerabilities:
            raise Exception("CVE not found.")

        cve = vulnerabilities[0]["cve"]

        metrics = cve.get("metrics", {})

        severity = "Unknown"
        score = 0.0
        exploitability = None
        impact = None

        if "cvssMetricV31" in metrics:

            metric = metrics["cvssMetricV31"][0]

            severity = metric["cvssData"]["baseSeverity"]
            score = metric["cvssData"]["baseScore"]
            exploitability = metric.get(
                "exploitabilityScore"
            )
            impact = metric.get("impactScore")

        elif "cvssMetricV30" in metrics:

            metric = metrics["cvssMetricV30"][0]

            severity = metric["cvssData"]["baseSeverity"]
            score = metric["cvssData"]["baseScore"]
            exploitability = metric.get(
                "exploitabilityScore"
            )
            impact = metric.get("impactScore")

        description = ""

        for desc in cve.get(
            "descriptions",
            [],
        ):

            if desc["lang"] == "en":

                description = desc["value"]

                break

        weaknesses = []

        for weakness in cve.get(
            "weaknesses",
            [],
        ):

            for desc in weakness.get(
                "description",
                [],
            ):

                if desc["lang"] == "en":

                    weaknesses.append(
                        desc["value"]
                    )

        weaknesses = list(
            dict.fromkeys(weaknesses)
        )

        references = list(

            dict.fromkeys(

                ref["url"]

                for ref in cve.get(
                    "references",
                    [],
                )

            )

        )

        references = references[:10]

        return {

            "cve": cve["id"],

            "severity": severity,

            "risk_level": ThreatMapper.get_risk_level(score),

            "cvss": score,

            "exploitability_score": exploitability,

            "impact_score": impact,

            "published": cve["published"],

            "last_modified": cve["lastModified"],

            "status": cve.get("vulnStatus"),

            "description": description,

            "weaknesses": weaknesses,

            "references": references,

            "ai_summary": None,

            "recommendations": [],
        }
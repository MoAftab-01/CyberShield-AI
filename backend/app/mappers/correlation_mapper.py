class CorrelationMapper:

    @staticmethod
    def correlate(data: dict) -> dict:

        score = 0

        reasons = []

        # CVSS

        cvss = data.get("cvss", 0)

        if cvss >= 9:

            score += 40

            reasons.append(
                f"Critical CVSS ({cvss})"
            )

        elif cvss >= 7:

            score += 25

            reasons.append(
                f"High CVSS ({cvss})"
            )

        # EPSS

        epss = data.get("epss_score", 0)

        if epss >= 0.90:

            score += 30

            reasons.append(
                f"Very High EPSS ({epss:.2%})"
            )

        elif epss >= 0.70:

            score += 20

            reasons.append(
                f"High EPSS ({epss:.2%})"
            )

        # CISA KEV

        if data.get("known_exploited"):

            score += 20

            reasons.append(
                "Listed in CISA KEV"
            )

        # Ransomware

        if (
            data.get("ransomware_use")
            and data["ransomware_use"] != "Unknown"
        ):

            score += 10

            reasons.append(
                "Associated with ransomware activity"
            )

        # Final Priority

        if score >= 80:

            priority = "PATCH IMMEDIATELY"

        elif score >= 60:

            priority = "HIGH PRIORITY"

        elif score >= 40:

            priority = "MEDIUM PRIORITY"

        else:

            priority = "LOW PRIORITY"

        assessment = (
            " | ".join(reasons)
            if reasons
            else "No significant indicators."
        )

        return {

            "priority": priority,

            "threat_assessment": assessment,
        }
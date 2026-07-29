class ThreatAggregator:

    @staticmethod
    def aggregate(
        local_score: int,
        vt_result: dict,
    ):

        final_score = local_score

        reasons = []

        confidence = 60

        malicious = vt_result.get("malicious", 0)
        suspicious = vt_result.get("suspicious", 0)

        if malicious > 0:
            penalty = min(malicious * 3, 50)
            final_score -= penalty

            confidence += 25

            reasons.append(
                f"VirusTotal detected {malicious} malicious vendors."
            )

        if suspicious > 0:
            penalty = min(suspicious * 2, 20)
            final_score -= penalty

            confidence += 10

            reasons.append(
                f"VirusTotal detected {suspicious} suspicious vendors."
            )

        final_score = max(0, min(final_score, 100))
        confidence = min(confidence, 100)

        if final_score >= 90:
            level = "Low"

        elif final_score >= 70:
            level = "Medium"

        elif final_score >= 40:
            level = "High"

        else:
            level = "Critical"

        if not reasons:
            reasons.append(
                "No known threat intelligence detections."
            )

        return {
            "final_score": final_score,
            "final_level": level,
            "confidence": confidence,
            "reasons": reasons,
        }
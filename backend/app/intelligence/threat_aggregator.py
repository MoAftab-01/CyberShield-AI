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

        # ``available`` is False when VirusTotal could not be consulted at all
        # - a rate limit, a rejected key, an outage. Its counters are zero in
        # that case, and reading them as "no detections" would tell the user
        # something was checked and came back clean when nothing was checked.
        # That is the one thing a security verdict must not do, so the absence
        # is reported as an absence and the confidence drops accordingly.
        if vt_result.get("available") is False:
            confidence -= 25
            reasons.append(
                vt_result.get("reason")
                or "VirusTotal reputation data was not available."
            )

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
        confidence = max(0, min(confidence, 100))

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
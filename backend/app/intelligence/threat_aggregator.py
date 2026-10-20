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
        available = vt_result.get("available")
        found = vt_result.get("found")
        is_internal = vt_result.get("is_internal", False)

        if available is False:
            threat_status = "unavailable"
            confidence -= 25
            reasons.append(
                vt_result.get("reason")
                or "VirusTotal reputation data was not available."
            )
        elif is_internal:
            threat_status = "inconclusive"
            reasons.append(
                vt_result.get("reason")
                or "Target points to internal/private network; public threat reputation is not applicable."
            )
        elif found is False:
            threat_status = "inconclusive"
            confidence = min(confidence, 60)
            reasons.append(
                "No previous scan records found in VirusTotal (inconclusive / unrated domain)."
            )
        elif malicious > 0:
            threat_status = "malicious"
            penalty = min(malicious * 3, 50)
            final_score -= penalty
            confidence += 25
            reasons.append(
                f"VirusTotal detected {malicious} malicious vendors."
            )
        elif suspicious > 0:
            threat_status = "suspicious"
            penalty = min(suspicious * 2, 20)
            final_score -= penalty
            confidence += 10
            reasons.append(
                f"VirusTotal detected {suspicious} suspicious vendors."
            )
        else:
            threat_status = "clean"
            confidence += 15
            reasons.append(
                "No known threat intelligence detections."
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

        return {
            "final_score": final_score,
            "final_level": level,
            "confidence": confidence,
            "threat_status": threat_status,
            "reasons": reasons,
        }
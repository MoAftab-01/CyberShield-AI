from typing import List


class PasswordRiskEngine:

    @staticmethod
    def calculate(
        password_length: int,
        has_uppercase: bool,
        has_lowercase: bool,
        has_number: bool,
        has_special_character: bool,
        entropy: float,
        dictionary_words: List[str],
        patterns: List[str],
    ):

        score = 100

        recommendations = []

        if password_length < 8:
            score -= 20
            recommendations.append(
                "Increase password length to at least 12 characters."
            )

        if not has_uppercase:
            score -= 10
            recommendations.append(
                "Include uppercase letters."
            )

        if not has_lowercase:
            score -= 10
            recommendations.append(
                "Include lowercase letters."
            )

        if not has_number:
            score -= 10
            recommendations.append(
                "Include numeric characters."
            )

        if not has_special_character:
            score -= 10
            recommendations.append(
                "Include special characters."
            )

        if entropy < 60:
            score -= 20
            recommendations.append(
                "Increase password randomness."
            )

        if dictionary_words:
            score -= 30
            recommendations.append(
                "Avoid common dictionary words."
            )

        if patterns:
            score -= 25
            recommendations.append(
                "Avoid predictable keyboard or sequential patterns."
            )

        score = max(score, 0)

        if score >= 90:
            level = "Excellent"
        elif score >= 75:
            level = "Good"
        elif score >= 50:
            level = "Moderate"
        elif score >= 25:
            level = "High"
        else:
            level = "Critical"

        return {
            "risk_score": score,
            "risk_level": level,
            "recommendations": recommendations,
        }
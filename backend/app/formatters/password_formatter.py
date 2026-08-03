from app.schemas.password_schema import PasswordResponse


class PasswordFormatter:

    @staticmethod
    def format(result):

        # ------------------------------------
        # LLM Responses
        # ------------------------------------

        if isinstance(result, dict):

            if "answer" in result:
                return result["answer"]

            if "message" in result:
                return result["message"]

        # ------------------------------------
        # Password Analysis
        # ------------------------------------

        if isinstance(result, PasswordResponse):

            return f"""
# 🔐 Password Security Analysis

## 💪 Strength

**{result.strength}**

Score: {result.score}/100

Entropy: {result.entropy:.2f}

Entropy Rating: {result.entropy_rating}

---

## 🔍 Password Composition

- Uppercase: {"✅" if result.has_uppercase else "❌"}

- Lowercase: {"✅" if result.has_lowercase else "❌"}

- Numbers: {"✅" if result.has_number else "❌"}

- Special Characters: {"✅" if result.has_special_character else "❌"}

---

## 🚨 Risks

Risk Score: {result.risk_score}

Risk Level: {result.risk_level}

Dictionary Words:
{", ".join(result.detected_dictionary_words) if result.detected_dictionary_words else "None"}

Patterns:
{", ".join(result.detected_patterns) if result.detected_patterns else "None"}

---

## 🛠️ Recommendations

{chr(10).join(f"- {item}" for item in result.recommendations)}
"""

        # ------------------------------------
        # Fallback
        # ------------------------------------

        return str(result)
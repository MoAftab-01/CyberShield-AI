class PasswordFormatter:

    @staticmethod
    def format(data) -> str:

        recommendations = ""

        for rec in getattr(data, "recommendations", []):
            recommendations += f"- {rec}\n"

        dictionary = getattr(
            data,
            "detected_dictionary_words",
            [],
        )

        patterns = getattr(
            data,
            "detected_patterns",
            [],
        )

        dictionary = (
            ", ".join(dictionary)
            if dictionary
            else "None"
        )

        patterns = (
            ", ".join(patterns)
            if patterns
            else "None"
        )

        return f"""# 🔐 Password Security Analysis

## 💪 Strength

**{data.strength}**

Score: {data.score}/100

Entropy: {data.entropy:.2f}

Entropy Rating: {data.entropy_rating}

---

## 🔍 Password Composition

- Uppercase: {"✅" if data.has_uppercase else "❌"}

- Lowercase: {"✅" if data.has_lowercase else "❌"}

- Numbers: {"✅" if data.has_number else "❌"}

- Special Characters: {"✅" if data.has_special_character else "❌"}

---

## 🚨 Risks

Risk Score: {data.risk_score}

Risk Level: {data.risk_level}

Dictionary Words: {dictionary}

Patterns: {patterns}

---

## 🛠️ Recommendations

{recommendations}
"""
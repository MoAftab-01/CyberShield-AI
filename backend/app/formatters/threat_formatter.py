class ThreatFormatter:

    @staticmethod
    def format(data) -> str:

        # ------------------------------------
        # LLM Responses
        # ------------------------------------

        if isinstance(data, dict):

            if "answer" in data:
                return data["answer"]

            if "message" in data:
                return data["message"]

            if "error" in data:
                return f"❌ {data['error']}"

        # ------------------------------------
        # Threat Lookup
        # ------------------------------------

        severity = data.get("severity", "Unknown")
        cvss = data.get("cvss", "N/A")

        risk = data.get("risk_level", "Unknown")

        vendor = data.get("vendor_project", "Unknown")

        product = data.get("product", "Unknown")

        exploited = (
            "Yes"
            if data.get("known_exploited")
            else "No"
        )

        epss = float(
            data.get(
                "epss_score",
                0,
            )
        ) * 100

        percentile = float(
            data.get(
                "epss_percentile",
                0,
            )
        ) * 100

        summary = data.get(
            "ai_summary",
            "No summary available.",
        )

        assessment = data.get(
            "threat_assessment",
            "Unavailable",
        )

        due = data.get(
            "due_date",
            "N/A",
        )

        github = len(
            data.get(
                "github_advisories",
                [],
            )
        )

        references = len(
            data.get(
                "references",
                [],
            )
        )

        recommendations = data.get(
            "recommendations",
            [],
        )

        recommendations_text = ""

        for item in recommendations:
            recommendations_text += (
                f"- {item}\n"
            )

        return f"""# 🛡️ {data.get("cve")}

## 🔴 Severity

**{severity}** (CVSS **{cvss}**)

---

## 🏢 Affected Product

**Vendor:** {vendor}

**Product:** {product}

---

## ⚠️ Threat Assessment

{assessment}

**Risk Level:** {risk}

---

## 📊 Exploitation Probability

**EPSS Score:** {epss:.2f}%

**Percentile:** Top {percentile:.2f}%

**Known Exploited:** {exploited}

---

## 🤖 AI Summary

{summary}

---

## 🛠️ Recommended Actions

{recommendations_text}

---

## 📅 Remediation Due

{due}

---

## 📚 Sources

- NVD

- CISA KEV

- GitHub Advisories ({github})

- Vendor References ({references})
"""
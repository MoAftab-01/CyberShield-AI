class URLFormatter:

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

        # ------------------------------------
        # URL Analysis
        # ------------------------------------

        recommendations = ""

        for rec in getattr(data, "recommendations", []):
            recommendations += f"- {rec}\n"

        summary = ""

        for item in getattr(data, "analysis_summary", []):
            summary += f"- {item}\n"

        keywords = getattr(data, "suspicious_keywords", [])

        if keywords:
            keywords = ", ".join(keywords)
        else:
            keywords = "None"

        return f"""# 🌐 URL Security Analysis

## 📍 Target

**URL:** {data.url}

**Domain:** {data.domain}

---

## 🛡️ Risk Assessment

**Risk Level:** {data.final_risk_level}

**Risk Score:** {data.final_risk_score}/100

**Confidence:** {data.confidence}%

---

## 🔍 URL Characteristics

- HTTPS: {"✅ Yes" if data.uses_https else "❌ No"}

- Contains IP Address: {"✅ Yes" if data.contains_ip_address else "❌ No"}

- URL Length: {data.url_length}

- Subdomains: {data.subdomain_count}

- Suspicious Keywords: {keywords}

---

## 🦠 VirusTotal

- Malicious: {data.virustotal_malicious}

- Suspicious: {data.virustotal_suspicious}

- Harmless: {data.virustotal_harmless}

---

## 🤖 AI Assessment

{summary}

---

## 🛠️ Recommended Actions

{recommendations}
"""
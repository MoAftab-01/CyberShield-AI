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

        status_label = getattr(data, "threat_status", "inconclusive").capitalize()
        is_private = getattr(data, "is_private_ip", False)

        return f"""# 🌐 URL Security Analysis

## 📍 Target

**URL:** {data.url}

**Domain:** {data.domain}

---

## 🛡️ Risk Assessment

**Risk Level:** {data.final_risk_level}

**Risk Score:** {data.final_risk_score}/100

**Confidence:** {data.confidence}%

**Threat Intelligence Status:** {status_label}

---

## 🔍 URL Characteristics

- HTTPS: {"✅ Yes" if data.uses_https else "❌ No"}

- Contains IP Address: {"✅ Yes" if data.contains_ip_address else "❌ No"}

- Internal / Private Network (SSRF Risk): {"🚨 Yes" if is_private else "✅ No (Public domain)"}

- URL Length: {data.url_length}

- Subdomains: {data.subdomain_count}

- Suspicious Keywords: {keywords}

---

## 🦠 VirusTotal Threat Intelligence

- Status: {status_label}

- Malicious Detections: {data.virustotal_malicious}

- Suspicious Detections: {data.virustotal_suspicious}

- Harmless / Clean: {data.virustotal_harmless}

---

## 🛡️ Verified Evidence & Findings

{summary}

---

## 🛠️ Recommended Actions

{recommendations}
"""
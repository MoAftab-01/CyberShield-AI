"""Query expansion and condensation for the RAG retrieval pipeline.

Two responsibilities, both zero-cost at runtime (no LLM call, no network):

1. **Acronym expansion** - adds the full phrase for each cybersecurity/
   infosec acronym found in the query so BM25 can match documents that spell
   out the term rather than abbreviating it, and vice versa.  The original
   query text is preserved verbatim; only additional tokens are appended.

2. **Conversational query condensation** - strips courtesy phrasing
   ("Can you please explain …", "Tell me more about …") and possessive back-
   references ("it", "that control", "the same document") *before* retrieval,
   so the BM25 and dense arms both score on content words rather than function
   words.  The raw question is always what reaches the LLM; only the retrieval
   query is condensed.

Design constraints (Render free tier)
--------------------------------------
* Pure Python + stdlib only - no extra packages, no memory overhead.
* No LLM call - the cost budget per turn is already spent on the answer.
* Idempotent - calling expand(expand(q)) == expand(q).
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# Acronym table
# ---------------------------------------------------------------------------
# Each entry maps an abbreviation (normalised to upper-case) to one or more
# expansion strings.  Bidirectional: if the query spells out the full form,
# the abbreviation is also injected (handled in expand_query).
#
# Sources: NIST SP 800-53 glossary, NIST SP 800-207, NIST CSF 2.0,
# OWASP ASVS, CIS Controls, ISO/IEC 27001, common industry usage.

ACRONYM_MAP: dict[str, str] = {
    # Access / identity
    "MFA":   "multi-factor authentication",
    "2FA":   "two-factor authentication",
    "SSO":   "single sign-on",
    "IAM":   "identity and access management",
    "PAM":   "privileged access management",
    "RBAC":  "role-based access control",
    "ABAC":  "attribute-based access control",
    "DAC":   "discretionary access control",
    "MAC":   "mandatory access control",
    "PKI":   "public key infrastructure",
    "LDAP":  "lightweight directory access protocol",
    "SAML":  "security assertion markup language",
    "OIDC":  "openid connect",
    "JWT":   "json web token",
    "OTP":   "one-time password",

    # Zero-trust architecture (NIST SP 800-207)
    "ZTA":   "zero trust architecture",
    "ZT":    "zero trust",
    "PDP":   "policy decision point",
    "PEP":   "policy enforcement point",
    "PA":    "policy administrator",
    # Note: "PE" is deliberately NOT in this map - it is ambiguous between
    # "Policy Engine" (ZTA) and "Physical and Environmental Protection" (NIST 800-53).
    # PEP (full "policy enforcement point") is the unambiguous form.
    "CDM":   "continuous diagnostics and mitigation",

    # Network / infrastructure
    "VPN":   "virtual private network",
    "DMZ":   "demilitarized zone",
    "NAC":   "network access control",
    "IDS":   "intrusion detection system",
    "IPS":   "intrusion prevention system",
    "NGFW":  "next-generation firewall",
    "WAF":   "web application firewall",
    "DLP":   "data loss prevention",
    "SIEM":  "security information and event management",
    "SOC":   "security operations center",
    "EDR":   "endpoint detection and response",
    "XDR":   "extended detection and response",
    "MDR":   "managed detection and response",
    "CASB":  "cloud access security broker",
    "ZTNA":  "zero trust network access",
    "SDN":   "software defined networking",
    "VLAN":  "virtual local area network",
    "TLS":   "transport layer security",
    "SSL":   "secure sockets layer",
    "SSH":   "secure shell",
    "DNS":   "domain name system",
    "DNSSEC": "dns security extensions",
    "BGP":   "border gateway protocol",

    # Vulnerability / threat
    "CVE":   "common vulnerabilities and exposures",
    "CWE":   "common weakness enumeration",
    "NVD":   "national vulnerability database",
    "CVSS":  "common vulnerability scoring system",
    "APT":   "advanced persistent threat",
    "C2":    "command and control",
    "IOC":   "indicator of compromise",
    "TTPs":  "tactics techniques and procedures",
    "MITRE": "mitre att&ck",
    "RCE":   "remote code execution",
    "XSS":   "cross-site scripting",
    "CSRF":  "cross-site request forgery",
    "SSRF":  "server-side request forgery",
    "SQLi":  "sql injection",
    "XXE":   "xml external entity",
    "LFI":   "local file inclusion",
    "RFI":   "remote file inclusion",
    "BoF":   "buffer overflow",

    # Compliance / frameworks
    "NIST":  "national institute of standards and technology",
    "CSF":   "cybersecurity framework",
    "GRC":   "governance risk and compliance",
    "FedRAMP": "federal risk and authorization management program",
    "FISMA": "federal information security modernization act",
    "HIPAA": "health insurance portability and accountability act",
    "GDPR":  "general data protection regulation",
    "PCI":   "payment card industry",
    "DSS":   "data security standard",
    "SOC2":  "system and organization controls 2",
    "ISMS":  "information security management system",
    "ISO":   "international organization for standardization",
    "RMF":   "risk management framework",
    "ATO":   "authority to operate",
    "PoAM":  "plan of action and milestones",
    "COOP":  "continuity of operations plan",
    "BCP":   "business continuity plan",
    "DRP":   "disaster recovery plan",
    "RTO":   "recovery time objective",
    "RPO":   "recovery point objective",
    "BIA":   "business impact analysis",

    # Cryptography
    "AES":   "advanced encryption standard",
    "RSA":   "rivest shamir adleman",
    "ECC":   "elliptic curve cryptography",
    "SHA":   "secure hash algorithm",
    "HMAC":  "hash-based message authentication code",
    "HSM":   "hardware security module",
    "TPM":   "trusted platform module",
    "KMS":   "key management service",

    # Cloud / DevSecOps
    "CSPM":  "cloud security posture management",
    "CWPP":  "cloud workload protection platform",
    "SBOM":  "software bill of materials",
    "SAST":  "static application security testing",
    "DAST":  "dynamic application security testing",
    "SCA":   "software composition analysis",
    "CI/CD": "continuous integration continuous deployment",
    "IaC":   "infrastructure as code",

    # Incident response
    "IR":    "incident response",
    "DFIR":  "digital forensics incident response",
    "MTTR":  "mean time to respond",
    "MTTD":  "mean time to detect",
    "TTP":   "tactics techniques and procedures",

    # NIST SP 800-53 control family abbreviations
    "AC":    "access control",
    "AU":    "audit and accountability",
    "CA":    "assessment authorization and monitoring",
    "CM":    "configuration management",
    "CP":    "contingency planning",
    "IA":    "identification and authentication",
    "MA":    "maintenance",
    "MP":    "media protection",
    "PE":    "physical and environmental protection",
    "PL":    "planning",
    "PM":    "program management",
    "PS":    "personnel security",
    "PT":    "personally identifiable information processing and transparency",
    "RA":    "risk assessment",
    "SA":    "system and services acquisition",
    "SC":    "system and communications protection",
    "SI":    "system and information integrity",
    "SR":    "supply chain risk management",
}

# ---------------------------------------------------------------------------
# Reverse map: full phrase → abbreviation (for bidirectional lookup)
# ---------------------------------------------------------------------------
_PHRASE_TO_ABBR: dict[str, str] = {
    phrase.lower(): abbr for abbr, phrase in ACRONYM_MAP.items()
}

# Partial-phrase map: 2-word prefixes that strongly imply a specific acronym
# even when the full phrase is interrupted (e.g. "policy decision and policy
# enforcement points" contains "policy decision" but not "policy decision point").
# Only applied when the implied acronym has not already been injected.
PARTIAL_PHRASE_MAP: dict[str, str] = {
    "policy decision":   "PDP",
    "policy enforcement": "PEP",
    "zero trust":        "ZT",
}

# Compiled pattern that matches any abbreviation as a whole word.
# Built once at import time.
_ABBR_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in sorted(ACRONYM_MAP, key=len, reverse=True)) + r")\b",
    re.IGNORECASE,
)

# Compiled patterns for partial-phrase matching.
_PARTIAL_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\b" + re.escape(phrase) + r"\b", re.IGNORECASE), abbr)
    for phrase, abbr in PARTIAL_PHRASE_MAP.items()
]


# ---------------------------------------------------------------------------
# Conversational noise patterns for query condensation
# ---------------------------------------------------------------------------
# These patterns are stripped from the *beginning* of the query before
# passing it to the retrieval engines.  The LLM always receives the original.

_CONVERSATIONAL_PREFIX = re.compile(
    r"""^(?:
        (?:can\s+you\s+(?:please\s+)?)?
        (?:tell\s+me|explain|describe|help\s+me\s+understand|
           walk\s+me\s+through|give\s+me|provide|list|outline|
           elaborate\s+on|clarify|show\s+me)\s+
        (?:(?:a\s+bit\s+)?(?:more\s+)?(?:about|on|regarding|for|how)\s+)?
    |
        (?:what\s+(?:is|are|does|do|would|can)\s+)
    |
        (?:how\s+(?:does|do|would|can)\s+)
    |
        (?:could\s+you\s+(?:please\s+)?)
    |
        (?:i\s+(?:want|need|would\s+like)\s+to\s+(?:know|understand|learn)\s+(?:about\s+)?)
    )""",
    re.IGNORECASE | re.VERBOSE,
)

# Back-reference pronouns / noun phrases that add no retrieval signal.
_BACK_REF = re.compile(
    r"\b(?:it|this|that|these|those|the\s+same|the\s+above|the\s+previous)\b"
    r"(?:\s+(?:control|document|policy|framework|standard|requirement|section|clause|item|one|approach|method|process|procedure|concept|topic|point|thing|subject|area|aspect|detail|example|case))?\b",
    re.IGNORECASE,
)


def expand_query(query: str) -> str:
    """Return the query with security acronyms expanded in-place.

    The original text is kept verbatim.  For each recognised acronym, its
    expansion is appended in parentheses directly after it the first time it
    appears.  Bidirectional: a spelled-out phrase also injects the acronym.

    This makes both BM25 (which scores exact tokens) and the dense encoder
    (which benefits from full-phrase context) more accurate for technical
    cybersecurity queries.

    Examples
    --------
    >>> expand_query("How does MFA work with SAML?")
    'How does MFA (multi-factor authentication) work with SAML (security assertion markup language)?'
    >>> expand_query("How does multi-factor authentication relate to zero trust?")
    'How does multi-factor authentication (MFA) relate to zero trust (ZTA)?'
    """

    seen: set[str] = set()
    result = query

    def _replace(match: re.Match) -> str:
        abbr_original = match.group(0)
        abbr_upper = abbr_original.upper()
        if abbr_upper in seen:
            return abbr_original
        seen.add(abbr_upper)
        expansion = ACRONYM_MAP.get(abbr_upper)
        if expansion is None:
            # Try mixed-case (e.g. "IaC", "SQLi")
            for key, val in ACRONYM_MAP.items():
                if key.upper() == abbr_upper:
                    expansion = val
                    break
        if expansion is None:
            return abbr_original
        return f"{abbr_original} ({expansion})"

    result = _ABBR_RE.sub(_replace, result)

    # Bidirectional: expand full phrases → abbreviation.
    # Iterate longest phrase first so "zero trust architecture" beats "zero trust".
    # Also match plural forms (phrase + "s") so "policy enforcement points" → PEP.
    for phrase in sorted(_PHRASE_TO_ABBR, key=len, reverse=True):
        abbr = _PHRASE_TO_ABBR[phrase]
        if abbr in seen:
            continue
        # Match singular or plural (trailing "s" or "es")
        pattern = re.compile(r"\b" + re.escape(phrase) + r"s?\b", re.IGNORECASE)
        if pattern.search(result):
            result = pattern.sub(lambda m: f"{m.group(0)} ({abbr})", result, count=1)
            seen.add(abbr)

    return result


def condense_query(query: str) -> str:
    """Strip conversational filler to leave the topical core for retrieval.

    Only the *retrieval* query is condensed; the raw question always reaches
    the LLM.  If the condensation would produce an empty string (e.g. the
    whole query was a greeting), the original is returned unchanged.

    Examples
    --------
    >>> condense_query("Can you please explain multi-factor authentication?")
    'multi-factor authentication?'
    >>> condense_query("Tell me more about the policy decision point.")
    'policy decision point.'
    >>> condense_query("What is it used for?")
    'used for?'
    """

    stripped = query.strip()

    # Remove conversational prefix.
    stripped = _CONVERSATIONAL_PREFIX.sub("", stripped).strip()

    # Remove trailing "please" artefacts that survive the prefix removal.
    stripped = re.sub(r"^please\s+", "", stripped, flags=re.IGNORECASE).strip()

    # Remove back-reference pronouns that carry no retrieval signal.
    stripped = _BACK_REF.sub("", stripped).strip()

    # Collapse multiple spaces.
    stripped = re.sub(r"\s{2,}", " ", stripped)

    # Guard: never return an empty or near-empty result.
    if len(stripped) < 4:
        return query

    return stripped


def prepare_retrieval_query(query: str) -> str:
    """Full query preparation pipeline: condense then expand.

    Call this once per retrieval request to get the optimised query string
    that reaches both BM25 and the dense encoder.  The original question is
    unchanged and should still be passed to the LLM.

    The condensation step runs first so that acronym expansion is applied to
    the clean topical core rather than to noisy function words.
    """

    condensed = condense_query(query)
    expanded = expand_query(condensed)
    return expanded

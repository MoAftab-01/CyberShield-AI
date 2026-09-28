"""Deterministic-first intent routing for CyberGPT.

Design goals (in priority order):

1. **Deterministic where possible.** Most cybersecurity requests are
   unambiguously recognisable from surface cues (a CVE id, a URL, the words
   "generate a password"). Rules handle those with zero LLM cost and zero
   latency, and they are unit-testable.
2. **Constrained LLM fallback.** Only when no rule fires *and* the question is
   substantial do we ask the model to classify. The call is a short prompt
   demanding a single JSON object, and every failure mode (timeout, bad JSON,
   unknown label) degrades to a deterministic default rather than an error.
3. **Observable.** Every decision records the intent, a confidence, the rule
   that fired and any entities extracted, so routing can be evaluated and
   debugged rather than guessed at.

This replaces the previous three-keyword classifier, which sent
"explain why long passwords are safer" to the password *analyzer* and sent
"hello" to the knowledge base.
"""

import json
import re
from dataclasses import dataclass, field

from app.agents.intents import Intent


@dataclass
class RoutingDecision:
    """The outcome of routing a single user question."""

    intent: Intent
    confidence: float
    source: str  # "rule" | "llm" | "default"
    reason: str
    password: str | None = None
    url: str | None = None
    cve: str | None = None
    password_length: int | None = None
    entities: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "intent": self.intent.value,
            "confidence": round(self.confidence, 3),
            "source": self.source,
            "reason": self.reason,
            "entities": {
                key: value
                for key, value in {
                    "password": "***" if self.password else None,
                    "url": self.url,
                    "cve": self.cve,
                    "password_length": self.password_length,
                }.items()
                if value is not None
            },
        }


# ---------------------------------------------------------------------------
# Entity patterns
# ---------------------------------------------------------------------------

CVE_PATTERN = re.compile(r"\bCVE-\d{4}-\d{4,}\b", re.IGNORECASE)
URL_PATTERN = re.compile(
    r"\bhttps?://[^\s<>\"')]+",
    re.IGNORECASE,
)
BARE_DOMAIN_PATTERN = re.compile(
    r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+"
    r"(?:com|net|org|io|co|dev|app|info|biz|ru|cn|xyz|top|online|site|link|click)\b"
    r"(?:/[^\s<>\"')]*)?",
    re.IGNORECASE,
)
PASSWORD_LENGTH_PATTERN = re.compile(
    r"\b(\d{1,3})\s*(?:character|char|digit|letter|symbol)s?\b",
    re.IGNORECASE,
)

# A value the user explicitly handed us to analyse, e.g.
#   "analyze this password: MyPassword123!"
#   'check the password "hunter2"'
#   "is hunter2 a good password"
PASSWORD_AFTER_COLON = re.compile(
    r"password\s*(?:is|:|=)\s*(?P<value>[^\s].{0,126}?)\s*$",
    re.IGNORECASE,
)
PASSWORD_QUOTED = re.compile(
    r"[\"'`](?P<value>[^\"'`\s]{4,128})[\"'`]",
)
PASSWORD_TRAILING_TOKEN = re.compile(
    r"\b(?:password|passphrase|pwd)\s+(?P<value>\S{4,128})\s*[.!?]?$",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Vocabulary
# ---------------------------------------------------------------------------

GREETING_PATTERN = re.compile(
    r"^\s*(?:hi|hey|hello|yo|sup|good\s+(?:morning|afternoon|evening)|"
    r"howdy|thanks|thank\s+you|thx|ok|okay|cool|nice|bye|goodbye|"
    r"who\s+are\s+you|what\s+can\s+you\s+do|help)\s*[!?.]*\s*$",
    re.IGNORECASE,
)

GENERATE_VERBS = (
    "generate", "create", "make", "give me", "suggest", "produce",
    "come up with", "need a", "want a", "new password", "random password",
)
ANALYZE_VERBS = (
    "analyze", "analyse", "check", "test", "evaluate", "assess", "rate",
    "score", "audit", "review", "how strong", "how secure", "is my password",
    "strength of", "crack",
)
ADVICE_VERBS = (
    "explain", "why", "how do", "how can", "how should", "what makes",
    "best practice", "best practices", "tips", "guidance", "advice",
    "recommend", "should i", "what is", "what are", "tell me about",
    "difference between", "understand",
)
SCAN_VERBS = (
    "scan", "check", "analyze", "analyse", "is this", "is it", "suspicious",
    "malicious", "safe", "phishing", "malware", "verdict", "reputation",
    "look up", "lookup", "investigate",
)
DOC_REFERENCES = (
    "uploaded document", "uploaded documents", "uploaded file",
    "uploaded files", "my document", "my documents", "my file", "my files",
    "knowledge base", "knowledgebase", "my pdf", "the pdf", "the document",
    "the documents", "these documents", "those documents", "the uploaded",
    "in the docs", "from the docs", "indexed document", "knowledge base",
)
DOC_VERBS = (
    "search", "find", "look up in", "according to", "summarize", "summarise",
    "compare", "quote", "cite", "what does the", "what do the",
)
THREAT_INTEL_PATTERN = re.compile(
    r"\b(?:latest|recent|newest|current|today'?s?|trending|emerging)\b"
    r".{0,40}\b(?:vulnerabilit|threat|cve|exploit|attack|malware|ransomware|"
    r"campaign|advisory|advisories)\w*\b"
    r"|\b(?:exploited in the wild|known exploited|actively exploited|"
    r"threat intel\w*|threat landscape|kev catalog)\b",
    re.IGNORECASE,
)
REPORT_PATTERN = re.compile(
    r"\b(?:generate|create|write|produce|build|prepare)\b.{0,30}"
    r"\b(?:report|summary|assessment|brief|overview)\b"
    r"|\breport\b.{0,20}\b(?:on|about|for)\b",
    re.IGNORECASE,
)
RECOMMENDATION_PATTERN = re.compile(
    r"\b(?:recommend|recommendation|advice|advise|harden|harden|secure my|"
    r"protect my|improve my|best practice|checklist|guidance|how do i secure|"
    r"how can i secure|how to secure|mitigat)\w*",
    re.IGNORECASE,
)
URL_ADVICE_PATTERN = re.compile(
    r"\b(?:url|link|domain|website|phishing|typosquat|homograph)\w*\b",
    re.IGNORECASE,
)
PASSWORD_TOPIC_PATTERN = re.compile(
    r"\b(?:password|passphrase|passwords|credential|credential|mfa|"
    r"multi-?factor|2fa|authentication)\w*\b",
    re.IGNORECASE,
)

#: Broad cybersecurity vocabulary, used only to pick a sensible default when
#: nothing else matches.
SECURITY_TOPIC_PATTERN = re.compile(
    r"\b(?:cyber|security|attack|attacker|threat|vulnerabilit|exploit|malware|"
    r"ransomware|phishing|virus|trojan|botnet|spyware|rootkit|firewall|"
    r"encryption|encrypt|crypto|tls|ssl|certificate|vpn|zero trust|"
    r"incident|forensics|siem|soc|pentest|penetration|xss|sqli|injection|"
    r"csrf|ssrf|owasp|nist|cisa|mitre|cvss|cve|patch|breach|leak|actor|"
    r"apt|backdoor|keylogger|ddos|network|endpoint|cloud|container|api|"
    r"access control|authentication|authorization|privilege|hardening|"
    r"secure|compliance|gdpr|iso 27001|risk)\w*\b",
    re.IGNORECASE,
)

#: Below this length a question is treated as chatter rather than a real
#: request, so we never spend an LLM call classifying "ok thanks".
MIN_LLM_ROUTING_LENGTH = 12


# ---------------------------------------------------------------------------
# Entity extraction
# ---------------------------------------------------------------------------

def extract_cve(question: str) -> str | None:
    match = CVE_PATTERN.search(question)
    return match.group(0).upper() if match else None


def extract_url(question: str) -> str | None:
    """Return the first URL the user appears to be asking about."""
    match = URL_PATTERN.search(question)
    if match:
        return match.group(0).rstrip(".,;:!?)")

    match = BARE_DOMAIN_PATTERN.search(question)
    if match:
        candidate = match.group(0).rstrip(".,;:!?)")
        # "owasp.org" inside an explanatory sentence is a citation, not a
        # scan target. Only treat it as a URL entity if it carries a path or
        # the user is clearly asking us to inspect it.
        if "/" in candidate:
            return candidate
        return candidate

    return None


def extract_password(question: str) -> str | None:
    """Extract a password the user explicitly supplied for analysis.

    Deliberately conservative: only returns a value when the user clearly
    handed one over. Returning a guess here would mean analysing the wrong
    string, which is the bug this replaces (the old agent analysed the whole
    sentence, e.g. ``"Analyze this password: MyPassword123!"``).
    """
    # "analyze this password: X" / "password is X" / "password = X"
    match = PASSWORD_AFTER_COLON.search(question)
    if match:
        candidate = match.group("value").strip().strip("'\"`")
        if candidate and "//" not in candidate and not candidate.lower().startswith("http"):
            return candidate

    # 'password "hunter2"'
    if PASSWORD_TOPIC_PATTERN.search(question):
        match = PASSWORD_QUOTED.search(question)
        if match:
            return match.group("value").strip()

    # "password hunter2"
    match = PASSWORD_TRAILING_TOKEN.search(question)
    if match:
        candidate = match.group("value").strip().strip("'\"`")
        # Avoid treating the topic word itself as the value.
        if candidate.lower() not in {
            "strength", "security", "manager", "policy", "policies",
            "requirements", "guidance", "advice", "best", "practices",
            "generator", "analysis", "reset", "management", "authentication",
            "safer", "safe", "strong", "weak",
        }:
            return candidate

    return None


def extract_password_length(question: str) -> int | None:
    match = PASSWORD_LENGTH_PATTERN.search(question)
    if not match:
        return None
    length = int(match.group(1))
    # Reject nonsense like "0 characters" or "999 characters".
    return length if 4 <= length <= 128 else None


def _contains_any(question: str, needles) -> str | None:
    lowered = question.lower()
    for needle in needles:
        if needle in lowered:
            return needle
    return None


def _is_document_request(question: str) -> bool:
    lowered = question.lower()
    has_reference = any(ref in lowered for ref in DOC_REFERENCES)
    has_verb = any(verb in lowered for verb in DOC_VERBS)
    # "search ... knowledge base" / "summarize the uploaded documents"
    return has_reference and has_verb


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

class IntentRouter:
    """Classifies a question into an :class:`Intent`."""

    @classmethod
    def classify(
        cls,
        question: str,
        allow_llm: bool = True,
    ) -> RoutingDecision:
        """Route a question. Never raises; always returns a decision."""

        question = (question or "").strip()

        if not question:
            return RoutingDecision(
                intent=Intent.GENERAL_CONVERSATION,
                confidence=1.0,
                source="rule",
                reason="empty question",
            )

        decision = cls._apply_rules(question)
        if decision is not None:
            return decision

        if allow_llm and len(question) >= MIN_LLM_ROUTING_LENGTH:
            decision = cls._classify_with_llm(question)
            if decision is not None:
                return decision

        return cls._default(question)

    # -- rules ------------------------------------------------------------

    @classmethod
    def _apply_rules(cls, question: str) -> RoutingDecision | None:
        lowered = question.lower()
        cve = extract_cve(question)
        url = extract_url(question)
        length = extract_password_length(question)

        # 1. CVE identifier present -> deterministic lookup, unless the user is
        #    asking about the wider threat landscape.
        if cve:
            if THREAT_INTEL_PATTERN.search(question):
                return RoutingDecision(
                    intent=Intent.THREAT_INTELLIGENCE,
                    confidence=0.85,
                    source="rule",
                    reason="CVE id plus threat-landscape wording",
                    cve=cve,
                    url=url,
                )
            return RoutingDecision(
                intent=Intent.CVE_LOOKUP,
                confidence=0.97,
                source="rule",
                reason="CVE identifier found",
                cve=cve,
            )

        # 2. Explicit "latest threats" style request.
        if THREAT_INTEL_PATTERN.search(question):
            return RoutingDecision(
                intent=Intent.THREAT_INTELLIGENCE,
                confidence=0.8,
                source="rule",
                reason="threat-landscape wording",
                url=url,
            )

        # 3. Password generation - an action, checked before analysis.
        if PASSWORD_TOPIC_PATTERN.search(question):
            if _contains_any(question, GENERATE_VERBS):
                return RoutingDecision(
                    intent=Intent.PASSWORD_GENERATION,
                    confidence=0.94,
                    source="rule",
                    reason="password plus generation verb",
                    password_length=length,
                )

        # 4. Password analysis - only when the user handed us a value or used
        #    an imperative analysis verb.
        if PASSWORD_TOPIC_PATTERN.search(question):
            password = extract_password(question)
            analyze_verb = _contains_any(question, ANALYZE_VERBS)
            if password or analyze_verb:
                return RoutingDecision(
                    intent=Intent.PASSWORD_ANALYSIS,
                    confidence=0.9 if password else 0.75,
                    source="rule",
                    reason=(
                        "password value supplied"
                        if password
                        else "password analysis verb"
                    ),
                    password=password,
                )

        # 5. URL scanning - needs a target plus scan intent.
        scan_verb = _contains_any(question, SCAN_VERBS)
        if url and scan_verb:
            return RoutingDecision(
                intent=Intent.URL_SCAN,
                confidence=0.9,
                source="rule",
                reason="URL plus scan intent",
                url=url,
            )

        # 6. Document-bound questions ("search my uploaded documents").
        if _is_document_request(question):
            if REPORT_PATTERN.search(question) or _contains_any(
                question, ("summarize", "summarise", "compare")
            ):
                return RoutingDecision(
                    intent=Intent.REPORT_GENERATION,
                    confidence=0.8,
                    source="rule",
                    reason="report verb over documents",
                )
            return RoutingDecision(
                intent=Intent.DOCUMENT_SEARCH,
                confidence=0.85,
                source="rule",
                reason="explicit document reference plus search verb",
            )

        # 7. Report generation from the knowledge base.
        if REPORT_PATTERN.search(question):
            return RoutingDecision(
                intent=Intent.REPORT_GENERATION,
                confidence=0.7,
                source="rule",
                reason="report verb",
            )

        # 8. Greetings and pure chatter.
        if GREETING_PATTERN.match(question):
            return RoutingDecision(
                intent=Intent.GENERAL_CONVERSATION,
                confidence=0.95,
                source="rule",
                reason="greeting or meta-question",
            )

        # 9. Password / URL topics that are explanatory rather than actionable.
        if PASSWORD_TOPIC_PATTERN.search(question) and _contains_any(
            question, ADVICE_VERBS
        ):
            return RoutingDecision(
                intent=Intent.PASSWORD_ADVICE,
                confidence=0.75,
                source="rule",
                reason="password topic with explanatory wording",
            )

        if URL_ADVICE_PATTERN.search(question) and _contains_any(
            question, ADVICE_VERBS
        ):
            return RoutingDecision(
                intent=Intent.URL_ADVICE,
                confidence=0.7,
                source="rule",
                reason="url topic with explanatory wording",
                url=url,
            )

        # 10. Explicit ask for guidance.
        if RECOMMENDATION_PATTERN.search(question):
            return RoutingDecision(
                intent=Intent.SECURITY_RECOMMENDATION,
                confidence=0.7,
                source="rule",
                reason="recommendation wording",
            )

        # 11. A general security question we did not recognise more narrowly.
        if SECURITY_TOPIC_PATTERN.search(question):
            return RoutingDecision(
                intent=Intent.GENERAL_SECURITY_QA,
                confidence=0.6,
                source="rule",
                reason="cybersecurity vocabulary",
            )

        return None

    # -- LLM fallback -----------------------------------------------------

    @classmethod
    def _classify_with_llm(cls, question: str) -> RoutingDecision | None:
        """Ask the model to classify, tolerating every failure mode."""

        # Imported lazily so that routing unit tests do not need an API key.
        from app.services.llm.provider_factory import ProviderFactory

        labels = ", ".join(intent.value for intent in Intent)

        prompt = (
            "Classify the user request into exactly one label.\n"
            f"Labels: {labels}\n"
            f"Request: {question[:400]}\n"
            'Reply with JSON only: {"intent":"<LABEL>","confidence":<0-1>}'
        )

        try:
            raw = ProviderFactory.get_provider().chat(
                prompt,
                max_tokens=60,
                temperature=0.0,
            )
        except Exception:
            return None

        try:
            payload = json.loads(_extract_json_object(raw))
            intent = Intent(str(payload.get("intent", "")).strip().upper())
            confidence = float(payload.get("confidence", 0.5))
        except (ValueError, TypeError, json.JSONDecodeError):
            return None

        confidence = min(max(confidence, 0.0), 1.0)

        return RoutingDecision(
            intent=intent,
            confidence=confidence,
            source="llm",
            reason="llm classification",
            url=extract_url(question),
            cve=extract_cve(question),
            password_length=extract_password_length(question),
        )

    # -- default ----------------------------------------------------------

    @classmethod
    def _default(cls, question: str) -> RoutingDecision:
        """Final fallback when neither rules nor the LLM produced an answer."""

        if SECURITY_TOPIC_PATTERN.search(question):
            return RoutingDecision(
                intent=Intent.GENERAL_SECURITY_QA,
                confidence=0.4,
                source="default",
                reason="unclassified but security-related",
                url=extract_url(question),
                cve=extract_cve(question),
            )

        return RoutingDecision(
            intent=Intent.GENERAL_CONVERSATION,
            confidence=0.4,
            source="default",
            reason="unclassified, not security-related",
        )


def _extract_json_object(raw: str) -> str:
    """Pull the first JSON object out of a model response.

    Models sometimes wrap JSON in prose or code fences; this keeps the router
    working without a fragile strict-parse dependency.
    """
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return raw
    return raw[start : end + 1]

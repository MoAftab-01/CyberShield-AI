"""Deterministic CyberGPT tools.

Each tool wraps capability the application *already* had, exposed on its own
page, so that CyberGPT can invoke it conversationally instead of pretending the
request is unanswerable. No tool re-implements business logic; every one
delegates to the existing service.

Two rules hold across all tools:

* **Tools never invent.** Password generation, password analysis and the
  CISA KEV lookup are deterministic. Their output is not passed through the
  LLM for "improvement", because a reworded security verdict is a different
  verdict.
* **Tool failures are reported, not disguised.** A failed upstream lookup
  returns an explicit error result rather than a confident-looking answer.
"""

from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.agents.intents import (
    BASIS_TOOL,
    Intent,
    TOOL_LABELS,
)
from app.agents.router import RoutingDecision


@dataclass
class ToolContext:
    """Everything a tool is allowed to touch."""

    db: Session
    user: object
    question: str
    decision: RoutingDecision
    conversation_id: int | None = None


@dataclass
class ToolResult:
    """The outcome of a tool invocation."""

    answer: str
    basis: str = BASIS_TOOL
    tool_used: str | None = None
    sources: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    suggestions: list = field(default_factory=list)
    ok: bool = True


# ---------------------------------------------------------------------------
# Password tools
# ---------------------------------------------------------------------------

async def password_generate(context: ToolContext) -> ToolResult:
    """Generate a cryptographically random password."""

    from app.services.password_service import PasswordService

    length = context.decision.password_length or 16

    generated = PasswordService.generate_secure(length)

    answer = (
        f"# 🔐 Generated Password\n\n"
        f"```\n{generated['password']}\n```\n\n"
        f"| Property | Value |\n"
        f"| --- | --- |\n"
        f"| Length | {generated['length']} characters |\n"
        f"| Estimated strength | **{generated['strength']}** |\n"
        f"| Score | {generated['score']}/100 |\n"
        f"| Entropy | {generated['entropy']:.1f} bits "
        f"({generated['entropy_rating']}) |\n\n"
        f"This password was produced locally with a cryptographically secure "
        f"random source and satisfies uppercase, lowercase, digit and symbol "
        f"requirements. It was never sent to an AI model.\n\n"
        f"**Store it in a password manager and enable MFA on the account.**"
    )

    return ToolResult(
        answer=answer,
        tool_used=TOOL_LABELS[Intent.PASSWORD_GENERATION],
        metadata={
            "password": generated["password"],
            "length": generated["length"],
            "score": generated["score"],
            "strength": generated["strength"],
            "entropy": round(generated["entropy"], 2),
            "regenerable": True,
        },
        suggestions=[
            "Analyze this password for weaknesses",
            "What makes a password strong?",
            "Explain password manager best practices",
        ],
    )


async def password_analyze(context: ToolContext) -> ToolResult:
    """Score a password the user supplied, entirely locally."""

    from app.formatters.password_formatter import PasswordFormatter
    from app.services.password_service import PasswordService

    password = context.decision.password

    if not password:
        # No value supplied - coach instead of failing. This is the case the
        # old implementation got wrong by analysing the whole sentence.
        return ToolResult(
            answer=(
                "I can score a password's length, character classes, entropy "
                "and known-weak patterns, but I need the actual value.\n\n"
                "Send it like this:\n\n"
                "> Analyze this password: `YourPasswordHere`\n\n"
                "**A safer option:** use the Password Analyzer page, or paste "
                "the password here only if you are comfortable sending it to "
                "this chat. Passwords are scored locally and are never sent to "
                "the AI model."
            ),
            tool_used=TOOL_LABELS[Intent.PASSWORD_ANALYSIS],
            metadata={"needs_password": True},
            suggestions=[
                "Generate a strong 20-character password",
                "What makes a password strong?",
            ],
        )

    analysis = PasswordService.analyze(
        db=context.db,
        current_user=context.user,
        password=password,
    )

    return ToolResult(
        answer=PasswordFormatter.format(analysis),
        tool_used=TOOL_LABELS[Intent.PASSWORD_ANALYSIS],
        metadata={
            "score": analysis.score,
            "strength": analysis.strength,
            "entropy": round(analysis.entropy, 2),
            "risk_score": analysis.risk_score,
            "risk_level": analysis.risk_level,
            "contains_dictionary_word": analysis.contains_dictionary_word,
            "contains_pattern": analysis.contains_pattern,
        },
        suggestions=[
            "Generate a stronger password",
            "How should I store passwords securely?",
        ],
    )


# ---------------------------------------------------------------------------
# URL tool
# ---------------------------------------------------------------------------

async def url_scan(context: ToolContext) -> ToolResult:
    """Run the URL risk assessment on a URL the user supplied."""

    from app.formatters.url_formatter import URLFormatter
    from app.services.url_service import URLService
    from app.utils.url_utils import is_valid_url

    url = context.decision.url or context.question.strip()

    if not is_valid_url(url):
        return ToolResult(
            answer=(
                f"I could not read `{url}` as a URL.\n\n"
                "Send something like:\n\n"
                "> Scan this URL: https://example.com/login"
            ),
            tool_used=TOOL_LABELS[Intent.URL_SCAN],
            metadata={"invalid_url": True},
            ok=False,
            suggestions=["Is this URL suspicious: http://example.com"],
        )

    try:
        analysis = await URLService.analyze(
            db=context.db,
            current_user=context.user,
            url=url,
        )
    except Exception as error:
        return ToolResult(
            answer=(
                f"The URL scan could not be completed for `{url}`.\n\n"
                f"Reason: {type(error).__name__}. This usually means an "
                "upstream threat-intelligence provider was unreachable or "
                "rate-limited. The local heuristics in the URL Scanner page "
                "still work without an API key."
            ),
            tool_used=TOOL_LABELS[Intent.URL_SCAN],
            metadata={"error": type(error).__name__},
            ok=False,
        )

    return ToolResult(
        answer=URLFormatter.format(analysis),
        tool_used=TOOL_LABELS[Intent.URL_SCAN],
        metadata={
            "url": analysis.url,
            "risk_level": analysis.final_risk_level,
            "risk_score": analysis.final_risk_score,
            "confidence": analysis.confidence,
        },
        suggestions=[
            "What are the signs of a phishing URL?",
            "How do I report a phishing site?",
        ],
    )


# ---------------------------------------------------------------------------
# Threat intelligence tools
# ---------------------------------------------------------------------------

async def cve_lookup(context: ToolContext) -> ToolResult:
    """Look a CVE up across NVD, CISA KEV, EPSS and GitHub advisories."""

    from app.formatters.threat_formatter import ThreatFormatter
    from app.services.threat_service import ThreatService

    cve = context.decision.cve

    if not cve:
        return ToolResult(
            answer=(
                "I can look up any CVE across NVD, the CISA KEV catalog, EPSS "
                "and GitHub advisories. Give me the identifier, for example:\n\n"
                "> What is CVE-2024-3400?"
            ),
            tool_used=TOOL_LABELS[Intent.CVE_LOOKUP],
            metadata={"needs_cve": True},
            ok=False,
        )

    try:
        record = ThreatService.get_cve(cve_id=cve, db=context.db)
    except Exception as error:
        return ToolResult(
            answer=(
                f"I could not retrieve `{cve}`.\n\n"
                f"Reason: {type(error).__name__}. NVD, CISA and EPSS are "
                "public APIs with their own rate limits; please retry shortly."
            ),
            tool_used=TOOL_LABELS[Intent.CVE_LOOKUP],
            metadata={"error": type(error).__name__, "cve": cve},
            ok=False,
        )

    known_exploited = bool(record.get("known_exploited"))

    suggestions = [
        f"How do I remediate {cve}?",
        "What are the latest known exploited vulnerabilities?",
    ]

    return ToolResult(
        answer=ThreatFormatter.format(record),
        tool_used=TOOL_LABELS[Intent.CVE_LOOKUP],
        metadata={
            "cve": record.get("cve"),
            "severity": record.get("severity"),
            "cvss": record.get("cvss"),
            "known_exploited": known_exploited,
            "risk_level": record.get("risk_level"),
            "epss_score": record.get("epss_score"),
        },
        suggestions=suggestions,
    )


async def threat_intelligence(context: ToolContext) -> ToolResult:
    """Report the most recently added CISA KEV entries.

    Answers "what are the latest known vulnerabilities?" from live data rather
    than from a model's training cutoff, which is the whole point of having a
    tool for it.
    """

    from app.clients.cisa_client import CISAClient

    if context.decision.cve:
        # A CVE id was named alongside threat wording - look it up directly.
        return await cve_lookup(context)

    entries = CISAClient.get_recent_kev(limit=8)

    if not entries:
        return ToolResult(
            answer=(
                "I could not reach the CISA Known Exploited Vulnerabilities "
                "catalog. It is a live public feed, so this is usually a "
                "temporary network or rate-limit issue - please retry.\n\n"
                "I would rather tell you the lookup failed than guess at "
                "which vulnerabilities are currently being exploited."
            ),
            tool_used=TOOL_LABELS[Intent.THREAT_INTELLIGENCE],
            metadata={"feed_unavailable": True},
            ok=False,
        )

    lines = [
        "# 🛡️ Most Recently Exploited Vulnerabilities",
        "",
        "Source: CISA Known Exploited Vulnerabilities catalog "
        "(live feed, newest additions first).",
        "",
        "| CVE | Vendor / Product | Added | Ransomware |",
        "| --- | --- | --- | --- |",
    ]

    for entry in entries:
        vendor_product = " / ".join(
            part
            for part in [entry.get("vendor"), entry.get("product")]
            if part
        ) or "Unknown"
        lines.append(
            f"| `{entry.get('cve')}` | {vendor_product} | "
            f"{entry.get('date_added') or 'n/a'} | "
            f"{entry.get('ransomware_use') or 'Unknown'} |"
        )

    lines += [
        "",
        "**Why this matters:** every entry here has confirmed evidence of "
        "exploitation in the wild, so CISA treats remediation as urgent - the "
        "`due_date` in the feed is a binding deadline for US federal agencies.",
        "",
        "Ask me about any of these by CVE id for severity, EPSS exploitation "
        "probability and remediation guidance.",
    ]

    return ToolResult(
        answer="\n".join(lines),
        tool_used=TOOL_LABELS[Intent.THREAT_INTELLIGENCE],
        metadata={
            "entries": [
                {"cve": entry.get("cve"), "date_added": entry.get("date_added")}
                for entry in entries
            ],
            "source": "CISA KEV",
        },
        suggestions=[
            f"What is {entries[0].get('cve')}?",
            "How should I prioritize patching?",
        ],
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

TOOL_REGISTRY = {
    Intent.PASSWORD_GENERATION: password_generate,
    Intent.PASSWORD_ANALYSIS: password_analyze,
    Intent.URL_SCAN: url_scan,
    Intent.CVE_LOOKUP: cve_lookup,
    Intent.THREAT_INTELLIGENCE: threat_intelligence,
}


async def run_tool(
    decision: RoutingDecision,
    context: ToolContext,
) -> ToolResult | None:
    """Execute the tool registered for this intent, if any."""

    tool = TOOL_REGISTRY.get(decision.intent)

    if tool is None:
        return None

    return await tool(context)


# ---------------------------------------------------------------------------
# Privacy helper
# ---------------------------------------------------------------------------

#: A fixed-width mask, deliberately not the password's own length. Rendering
#: one bullet per character would hide the value but publish its length, and
#: length is the single most useful fact about a password to someone trying to
#: crack it.
MASK = "•" * 12


def redact_secrets(text: str, decision: RoutingDecision) -> str:
    """Remove values that must not be persisted in conversation history.

    A password the user pasted for analysis is needed in memory to score it,
    but storing it verbatim in the chat log would turn a stateless check into a
    durable plaintext credential store. It is masked before the message is
    written to the database.
    """

    if decision.intent is not Intent.PASSWORD_ANALYSIS:
        return text

    if not decision.password:
        return text

    return text.replace(decision.password, MASK)

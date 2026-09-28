"""Intent taxonomy for the CyberGPT orchestrator.

The taxonomy separates three fundamentally different kinds of request, because
they need different handling:

* ``TOOL_INTENTS``  - the user wants an *action* performed (generate a password,
  scan a URL, look up a CVE). Handled by a deterministic tool, not by retrieval.
* ``KNOWLEDGE_INTENTS`` - the user wants an *explanation*. Retrieval is attempted
  first, with a clearly-labelled general-knowledge fallback.
* ``CONVERSATION_INTENTS`` - greetings and meta-chatter. No retrieval at all.

Keeping this distinction explicit is what stops CyberGPT from answering
"generate a strong password" with "the documents do not contain enough
information".
"""

from enum import Enum


class Intent(str, Enum):
    """Every routable CyberGPT capability."""

    # --- conversational -------------------------------------------------
    GENERAL_CONVERSATION = "GENERAL_CONVERSATION"

    # --- actions (deterministic tools) ----------------------------------
    PASSWORD_GENERATION = "PASSWORD_GENERATION"
    PASSWORD_ANALYSIS = "PASSWORD_ANALYSIS"
    URL_SCAN = "URL_SCAN"
    CVE_LOOKUP = "CVE_LOOKUP"
    THREAT_INTELLIGENCE = "THREAT_INTELLIGENCE"

    # --- knowledge (retrieval-first, general fallback) ------------------
    RAG_KNOWLEDGE_QUERY = "RAG_KNOWLEDGE_QUERY"
    DOCUMENT_SEARCH = "DOCUMENT_SEARCH"
    GENERAL_SECURITY_QA = "GENERAL_SECURITY_QA"
    SECURITY_RECOMMENDATION = "SECURITY_RECOMMENDATION"
    PASSWORD_ADVICE = "PASSWORD_ADVICE"
    URL_ADVICE = "URL_ADVICE"
    REPORT_GENERATION = "REPORT_GENERATION"


#: Intents handled by a deterministic tool rather than by the LLM.
TOOL_INTENTS = frozenset(
    {
        Intent.PASSWORD_GENERATION,
        Intent.PASSWORD_ANALYSIS,
        Intent.URL_SCAN,
        Intent.CVE_LOOKUP,
        Intent.THREAT_INTELLIGENCE,
    }
)

#: Intents that should attempt knowledge-base retrieval first.
KNOWLEDGE_INTENTS = frozenset(
    {
        Intent.RAG_KNOWLEDGE_QUERY,
        Intent.DOCUMENT_SEARCH,
        Intent.GENERAL_SECURITY_QA,
        Intent.SECURITY_RECOMMENDATION,
        Intent.PASSWORD_ADVICE,
        Intent.URL_ADVICE,
        Intent.REPORT_GENERATION,
    }
)

#: Intents answered purely conversationally - retrieval is never useful here.
CONVERSATION_INTENTS = frozenset({Intent.GENERAL_CONVERSATION})

#: Intents where the user explicitly asked about *their* documents, so a
#: general-knowledge answer is not an acceptable substitute.
#:
#: ``RAG_KNOWLEDGE_QUERY`` is deliberately absent. It is the default label for
#: "a knowledge question", and treating it as document-bound would send every
#: unrecognised question down the knowledge-base path regardless of whether the
#: corpus covers it - which is precisely the behaviour that made the assistant
#: answer everything as if it were a search over a handful of PDFs. Such
#: questions go through the confidence gate instead.
DOCUMENT_BOUND_INTENTS = frozenset(
    {
        Intent.DOCUMENT_SEARCH,
        Intent.REPORT_GENERATION,
    }
)

#: Human-readable label shown to the user when a tool was executed.
TOOL_LABELS = {
    Intent.PASSWORD_GENERATION: "Password Generator",
    Intent.PASSWORD_ANALYSIS: "Password Analyzer",
    Intent.URL_SCAN: "URL Scanner",
    Intent.CVE_LOOKUP: "CVE Lookup",
    Intent.THREAT_INTELLIGENCE: "Threat Intelligence",
}

#: Short description of where the answer came from. Rendered by the UI so the
#: user always knows whether they are reading their documents or model knowledge.
BASIS_DOCUMENT = "document"
BASIS_GENERAL = "general_knowledge"
BASIS_TOOL = "tool"
BASIS_CONVERSATION = "conversation"

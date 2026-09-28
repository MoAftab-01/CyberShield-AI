"""Tool dispatch tests.

A tool is the one path in the assistant where the answer is not written by a
model. That property is what these tests protect: several of them assert that a
tool produced its answer *without* the LLM being reachable at all, because a
tool result that has been through a model is a reworded verdict, not a verdict.

Every tool is exercised through ``run_tool`` rather than by calling it directly,
so the registry itself is covered - a tool that exists but is not registered is
unreachable from the API and this is where that shows up.
"""

import asyncio

import pytest

from app.agents.intents import Intent
from app.agents.router import IntentRouter
from app.agents.tools import (
    TOOL_REGISTRY,
    ToolContext,
    ToolResult,
    redact_secrets,
    run_tool,
)


def call_tool(question, db, user, **overrides):
    """Route ``question`` and invoke whichever tool the router selected."""

    decision = IntentRouter.classify(question, allow_llm=False)

    context = ToolContext(
        db=db,
        user=user,
        question=question,
        decision=decision,
    )

    for key, value in overrides.items():
        setattr(context, key, value)

    return asyncio.run(run_tool(decision, context)), decision


class TestToolRegistry:

    def test_every_tool_intent_has_a_registered_tool(self):
        """An intent the router can select must have something to run.

        Otherwise the orchestrator dispatches to a tool, gets ``None``, and the
        request fails with an unhandled error.
        """

        from app.agents.intents import TOOL_INTENTS

        for intent in TOOL_INTENTS:
            assert intent in TOOL_REGISTRY, f"{intent} has no tool"

    def test_a_knowledge_intent_has_no_tool(self):
        """``run_tool`` returns None so the caller can fall through."""

        decision = IntentRouter.classify(
            "How does zero trust work?", allow_llm=False
        )

        result = asyncio.run(
            run_tool(
                decision,
                ToolContext(
                    db=None, user=None, question="x", decision=decision
                ),
            )
        )

        assert result is None


class TestPasswordGeneration:

    def test_generation_needs_no_model(self, db_session, user_factory, stub_llm):
        user = user_factory()

        result, decision = call_tool(
            "Generate a strong password", db_session, user
        )

        assert result is not None
        assert result.tool_used == "Password Generator"
        assert stub_llm == [], "password generation must not call the model"

    def test_generated_password_meets_the_requested_length(
        self, db_session, user_factory
    ):
        result, _ = call_tool(
            "generate a 24 character password", db_session, user_factory()
        )

        assert result.metadata["length"] == 24
        assert len(result.metadata["password"]) == 24

    def test_the_password_is_returned_as_metadata_for_the_ui(
        self, db_session, user_factory
    ):
        result, _ = call_tool("Generate a password", db_session, user_factory())

        assert result.metadata["password"]
        assert result.metadata["regenerable"] is True

    def test_two_generations_differ(self, db_session, user_factory):
        user = user_factory()

        first, _ = call_tool("Generate a password", db_session, user)
        second, _ = call_tool("Generate a password", db_session, user)

        assert first.metadata["password"] != second.metadata["password"]

    def test_an_absurd_length_does_not_hang_the_request(
        self, db_session, user_factory
    ):
        """The router bounds the length; the tool must not be the weak link."""

        result, _ = call_tool(
            "generate a 100000 character password", db_session, user_factory()
        )

        assert result.metadata["length"] <= 512


class TestPasswordAnalysis:

    def test_advice_is_not_treated_as_a_password(
        self, db_session, user_factory, stub_llm
    ):
        """The original defect: the sentence was scored as the password."""

        result, decision = call_tool(
            "Why are long passwords safer?", db_session, user_factory()
        )

        # Whatever the routing decides, it must not be a password score.
        if decision.intent is Intent.PASSWORD_ANALYSIS:
            assert result.metadata.get("needs_password") is True
        else:
            assert result is None

    def test_a_missing_value_produces_coaching_not_a_failure(
        self, db_session, user_factory
    ):
        result, _ = call_tool(
            "analyze password", db_session, user_factory()
        )

        assert result.ok is True
        assert result.metadata["needs_password"] is True
        assert "Analyze this password" in result.answer

    def test_a_supplied_password_is_scored_locally(
        self, db_session, user_factory, stub_llm
    ):
        result, decision = call_tool(
            "analyze password: Tr0ub4dor&3", db_session, user_factory()
        )

        assert decision.intent is Intent.PASSWORD_ANALYSIS
        assert "score" in result.metadata
        assert stub_llm == [], "a password must never be sent to the model"

    def test_a_weak_password_scores_below_a_strong_one(
        self, db_session, user_factory
    ):
        user = user_factory()

        weak, _ = call_tool("analyze password: password123", db_session, user)
        strong, _ = call_tool(
            "analyze password: 7Kq#vL2mX!9pRz4T", db_session, user
        )

        assert weak.metadata["score"] < strong.metadata["score"]

    def test_the_password_is_not_persisted_by_the_tool(
        self, db_session, user_factory
    ):
        """The tool returns the score; only ``metadata`` carries the value,
        and the orchestrator redacts the stored message separately."""

        result, _ = call_tool(
            "analyze password: Tr0ub4dor&3", db_session, user_factory()
        )

        assert "Tr0ub4dor&3" not in result.answer


class TestUrlScan:

    def test_an_unreadable_url_is_reported_not_scanned(
        self, db_session, user_factory
    ):
        """``scan http://..`` routes here but is not a usable URL.

        The router looks for the shape of a URL, which this has; validation
        then rejects it, and the tool must say so rather than pass a malformed
        host to the threat-intelligence providers.
        """

        result, decision = call_tool("scan http://..", db_session, user_factory())

        assert decision.intent is Intent.URL_SCAN
        assert result is not None
        assert result.ok is False
        assert result.metadata.get("invalid_url") is True
        assert "could not read" in result.answer

    def test_a_valid_url_reaches_the_url_service(
        self, db_session, user_factory, monkeypatch
    ):
        from types import SimpleNamespace

        from app.services import url_service

        seen = {}

        async def fake_analyze(db, current_user, url):
            seen["url"] = url
            return SimpleNamespace(
                url=url,
                domain="example.com",
                final_risk_level="Low",
                final_risk_score=5,
                confidence=80,
                recommendations=[],
                analysis_summary=[],
                suspicious_keywords=[],
                uses_https=True,
                contains_ip_address=False,
                url_length=len(url),
                subdomain_count=0,
                virustotal_malicious=0,
                virustotal_suspicious=0,
                virustotal_harmless=70,
            )

        monkeypatch.setattr(url_service.URLService, "analyze", fake_analyze)

        result, decision = call_tool(
            "scan https://example.com/login", db_session, user_factory()
        )

        assert decision.intent is Intent.URL_SCAN
        assert seen["url"] == "https://example.com/login"
        assert result.metadata["risk_level"] == "Low"

    def test_an_upstream_failure_is_disclosed_not_hidden(
        self, db_session, user_factory, monkeypatch
    ):
        from app.services import url_service

        async def exploding_analyze(db, current_user, url):
            raise RuntimeError("provider unreachable")

        monkeypatch.setattr(url_service.URLService, "analyze", exploding_analyze)

        result, _ = call_tool(
            "scan https://example.com", db_session, user_factory()
        )

        assert result.ok is False
        assert "could not be completed" in result.answer
        assert "RuntimeError" in result.answer


class TestCveLookup:

    def test_a_cve_is_passed_through_to_the_threat_service(
        self, db_session, user_factory, monkeypatch
    ):
        from app.services import threat_service

        seen = {}

        def fake_get_cve(cve_id, db):
            seen["cve"] = cve_id
            return {
                "cve": cve_id,
                "severity": "CRITICAL",
                "cvss": 10.0,
                "known_exploited": True,
                "risk_level": "Critical",
                "epss_score": 0.97,
            }

        monkeypatch.setattr(
            threat_service.ThreatService, "get_cve", staticmethod(fake_get_cve)
        )

        result, decision = call_tool(
            "What is CVE-2021-44228?", db_session, user_factory()
        )

        assert seen["cve"] == "CVE-2021-44228"
        assert result.metadata["known_exploited"] is True
        assert result.metadata["severity"] == "CRITICAL"

    def test_an_upstream_failure_is_disclosed(self, db_session, user_factory, monkeypatch):
        from app.services import threat_service

        def exploding(cve_id, db):
            raise RuntimeError("NVD rate limited")

        monkeypatch.setattr(
            threat_service.ThreatService, "get_cve", staticmethod(exploding)
        )

        result, _ = call_tool(
            "What is CVE-2021-44228?", db_session, user_factory()
        )

        assert result.ok is False
        assert "could not retrieve" in result.answer
        assert "RuntimeError" in result.answer

    def test_asking_for_a_cve_without_one_asks_for_it(
        self, db_session, user_factory
    ):
        """Reached by forcing the intent, since the router needs an id to
        select this tool in the first place."""

        decision = IntentRouter.classify("x", allow_llm=False)
        decision.intent = Intent.CVE_LOOKUP

        result = asyncio.run(
            run_tool(
                decision,
                ToolContext(
                    db=db_session,
                    user=user_factory(),
                    question="tell me about that vulnerability",
                    decision=decision,
                ),
            )
        )

        assert result.ok is False
        assert result.metadata["needs_cve"] is True
        assert "CVE-2024-3400" in result.answer


class TestThreatIntelligence:

    def test_the_feed_is_reported_with_its_source(
        self, db_session, user_factory, monkeypatch
    ):
        from app.clients import cisa_client

        monkeypatch.setattr(
            cisa_client.CISAClient,
            "get_recent_kev",
            staticmethod(
                lambda limit=8: [
                    {
                        "cve": "CVE-2024-0001",
                        "vendor": "Acme",
                        "product": "Widget",
                        "date_added": "2024-01-01",
                        "ransomware_use": "Known",
                    }
                ]
            ),
        )

        result, _ = call_tool(
            "What are the latest threats?", db_session, user_factory()
        )

        assert result.metadata["source"] == "CISA KEV"
        assert "CVE-2024-0001" in result.answer
        assert "live feed" in result.answer

    def test_an_unreachable_feed_is_admitted(
        self, db_session, user_factory, monkeypatch
    ):
        """The whole value of the tool is that it does not guess."""

        from app.clients import cisa_client

        monkeypatch.setattr(
            cisa_client.CISAClient,
            "get_recent_kev",
            staticmethod(lambda limit=8: []),
        )

        result, _ = call_tool(
            "What are the latest threats?", db_session, user_factory()
        )

        assert result.ok is False
        assert result.metadata["feed_unavailable"] is True
        assert "rather tell you the lookup failed than guess" in result.answer


class TestRedactSecrets:

    def test_a_pasted_password_is_masked_before_storage(self):
        decision = IntentRouter.classify(
            "analyze password: Tr0ub4dor&3", allow_llm=False
        )

        stored = redact_secrets("analyze password: Tr0ub4dor&3", decision)

        assert "Tr0ub4dor&3" not in stored
        assert "•" in stored

    def test_the_mask_does_not_reveal_the_length(self):
        """A masked value of known length is a meaningful hint."""

        long_decision = IntentRouter.classify(
            "analyze password: " + "a" * 40, allow_llm=False
        )
        short_decision = IntentRouter.classify(
            "analyze password: " + "a" * 8, allow_llm=False
        )

        long_mask = redact_secrets("x" + "a" * 40, long_decision)
        short_mask = redact_secrets("x" + "a" * 8, short_decision)

        assert len(long_mask) == len(short_mask)

    def test_an_ordinary_question_is_untouched(self):
        decision = IntentRouter.classify(
            "How does TLS work?", allow_llm=False
        )

        assert redact_secrets("How does TLS work?", decision) == "How does TLS work?"

    def test_an_analysis_request_without_a_value_is_untouched(self):
        decision = IntentRouter.classify("analyze password", allow_llm=False)

        assert redact_secrets("analyze password", decision) == "analyze password"

    def test_redaction_only_replaces_the_password(self):
        decision = IntentRouter.classify(
            "analyze password: hunter2", allow_llm=False
        )

        stored = redact_secrets("analyze password: hunter2", decision)

        assert stored.startswith("analyze password: ")
        assert "hunter2" not in stored


class TestToolResultContract:

    def test_every_registered_tool_returns_a_tool_result(
        self, db_session, user_factory, monkeypatch
    ):
        """A tool returning a bare string would break the route's schema."""

        from app.clients import cisa_client
        from app.services import threat_service, url_service

        monkeypatch.setattr(
            cisa_client.CISAClient,
            "get_recent_kev",
            staticmethod(lambda limit=8: []),
        )
        monkeypatch.setattr(
            threat_service.ThreatService,
            "get_cve",
            staticmethod(
                lambda cve_id, db: {"cve": cve_id, "severity": "HIGH"}
            ),
        )

        async def fake_analyze(db, current_user, url):
            raise RuntimeError("offline")

        monkeypatch.setattr(url_service.URLService, "analyze", fake_analyze)

        user = user_factory()

        questions = [
            "Generate a strong password",
            "analyze password: Tr0ub4dor&3",
            "analyze password",
            "scan https://example.com",
            "What is CVE-2021-44228?",
            "What are the latest threats?",
        ]

        for question in questions:
            result, decision = call_tool(question, db_session, user)

            assert result is not None, question
            assert isinstance(result, ToolResult), question
            assert isinstance(result.answer, str) and result.answer, question
            assert isinstance(result.metadata, dict), question
            assert isinstance(result.suggestions, list), question
            assert result.basis, question
            assert decision.intent in TOOL_REGISTRY, question

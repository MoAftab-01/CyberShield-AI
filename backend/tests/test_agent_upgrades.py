"""Focused tests for Password Agent, URL Agent, and Orchestrator enhancements.

Covers:
- Password privacy (no raw passwords sent to LLM, secret masking in history/RAG)
- Secure generation (uses secrets module, bounds, entropy, character classes)
- URL edge cases & SSRF safeguards (private IPs, loopback, metadata, invalid schemes)
- Threat intelligence status distinctions (malicious, suspicious, clean, inconclusive, unavailable)
- Orchestration resilience (tool selection, malformed LLM outputs, service outages)
"""

import asyncio
import pytest

from app.agents.intents import Intent
from app.agents.router import IntentRouter, extract_password, extract_url
from app.agents.tools import ToolContext, redact_secrets, password_generate, url_scan
from app.intelligence.threat_aggregator import ThreatAggregator
from app.services.password_service import PasswordService
from app.formatters.password_formatter import PasswordFormatter
from app.utils.password_utils import calculate_score, password_strength, calculate_entropy
from app.utils.url_utils import (
    is_valid_url,
    is_private_or_internal_host,
    contains_punycode,
    has_non_standard_port,
    detect_keywords,
    calculate_url_risk,
)
from app.integrations.virustotal import VirusTotalClient


def run(coro):
    return asyncio.run(coro)


# ===========================================================================
# 1. Password Agent: Secure Generation & Privacy
# ===========================================================================

class TestPasswordSecurityAndPrivacy:

    def test_password_generation_uses_secrets_never_llm(self, stub_llm):
        """Generation must be 100% deterministic and local."""
        result = PasswordService.generate_secure(length=20)
        assert len(result["password"]) == 20
        assert result["score"] >= 4
        assert result["strength"] in {"Strong", "Very Strong"}
        assert stub_llm == [], "Password generation must never call an LLM"

    def test_password_generation_bounds_lengths(self):
        """Requested lengths below 8 or above 128 must be safely clamped."""
        short_res = PasswordService.generate_secure(length=3)
        assert len(short_res["password"]) == PasswordService.MIN_GENERATED_LENGTH

        long_res = PasswordService.generate_secure(length=500)
        assert len(long_res["password"]) == PasswordService.MAX_GENERATED_LENGTH

    def test_generated_passwords_meet_character_classes(self):
        """Generated passwords must contain uppercase, lowercase, numbers and symbols."""
        for _ in range(10):
            res = PasswordService.generate_secure(16)
            pwd = res["password"]
            assert any(c.isupper() for c in pwd)
            assert any(c.islower() for c in pwd)
            assert any(c.isdigit() for c in pwd)
            assert any(c in "!@#$%^&*()-_=+[]{}?" for c in pwd)

    def test_raw_passwords_never_sent_to_llm_during_classification(self, stub_llm):
        """Intent classifier must extract/redact passwords before calling LLM."""
        decision = IntentRouter.classify("Is SecretP@ssw0rd123! a strong password?", allow_llm=True)
        # Should be caught by rule or direct entity extraction without leaking password to LLM
        for call in stub_llm:
            assert "SecretP@ssw0rd123!" not in str(call)

    def test_redact_secrets_masks_across_different_intents(self):
        """Password should be redacted regardless of whether intent is analysis or advice."""
        decision = IntentRouter.classify("Why is Hunter2! a bad password?", allow_llm=False)
        masked = redact_secrets("Why is Hunter2! a bad password?", decision)
        assert "Hunter2!" not in masked
        assert "••••••••••••" in masked


    def test_deterministic_strength_checks_penalize_common_patterns(self):
        """Passwords with dictionary words or keyboard sequences must be penalized."""
        # Simple dictionary word with common sequence
        score_weak = calculate_score("Password123!")
        assert score_weak <= 2
        assert password_strength(score_weak) == "Weak"

        # Strong high-entropy random password
        score_strong = calculate_score("X9#mK2$vLq8*pZ1w")
        assert score_strong >= 4
        assert password_strength(score_strong) in {"Strong", "Very Strong"}

    def test_explain_findings_does_not_require_raw_password(self, stub_llm):
        """Actionable explanations must operate solely on sanitized findings."""
        findings = {
            "strength": "Weak",
            "length": 8,
            "entropy": 25.5,
            "entropy_rating": "Very Weak",
            "has_uppercase": True,
            "has_lowercase": True,
            "has_number": True,
            "has_special_character": False,
            "detected_dictionary_words": ["password"],
            "detected_patterns": ["Sequential Numbers (123456)"],
            "risk_level": "High",
            "recommendations": ["Avoid dictionary words", "Increase length to at least 16"],
        }
        explanation = PasswordService.explain_findings(findings)
        assert explanation is not None
        assert isinstance(explanation, str)

    def test_conversation_title_masks_raw_password_in_new_conversation(self, db_session, user_factory):
        """When starting a new conversation with a password in the prompt, the title must be masked."""
        from app.agents.orchestrator import CyberGPTOrchestrator
        from app.database.conversation_crud import ConversationCRUD

        user = user_factory()
        orchestrator = CyberGPTOrchestrator()
        result = run(
            orchestrator.handle(
                question="Why is P@ssw0rd123! considered weak?",
                db=db_session,
                user_id=user.id,
            )
        )
        conv_id = result["conversation_id"]
        conv = ConversationCRUD.get_conversation(db=db_session, conversation_id=conv_id, user_id=user.id)
        assert conv is not None
        assert "P@ssw0rd123!" not in conv.title
        assert "••••••••••••" in conv.title

    def test_password_score_displayed_out_of_5(self, db_session, user_factory):
        """Password score is on a 0-5 tier and must be formatted as /5, never /100."""
        gen_text = PasswordService.generate(16)["answer"]
        assert "/5" in gen_text
        assert "/100" not in gen_text

        analysis_res = PasswordService.analyze(db=db_session, current_user=user_factory(), password="TestPassword123!")
        formatted = PasswordFormatter.format(analysis_res)
        assert f"Score: {analysis_res.score}/5" in formatted
        assert f"Score: {analysis_res.score}/100" not in formatted

        tool_decision = IntentRouter.classify("generate a strong password", allow_llm=False)
        tool_ctx = ToolContext(db=db_session, user=user_factory(), question="generate a strong password", decision=tool_decision)
        tool_result = run(password_generate(tool_ctx))
        assert "/5" in tool_result.answer
        assert "/100" not in tool_result.answer


# ===========================================================================
# 2. URL Agent: Validation, SSRF Safeguards & Heuristics
# ===========================================================================

class TestURLValidationAndSSRF:

    @pytest.mark.parametrize(
        "safe_url",
        [
            "https://example.com",
            "http://example.org/path?q=1",
            "sub.domain.example.co.uk",
            "https://test.com:8443/login",
        ],
    )
    def test_valid_urls_are_accepted(self, safe_url):
        assert is_valid_url(safe_url) is True

    @pytest.mark.parametrize(
        "dangerous_or_invalid",
        [
            "",
            "   ",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "gopher://127.0.0.1:70/",
            "data:text/html,test",
        ],
    )
    def test_dangerous_schemes_and_malformed_urls_rejected(self, dangerous_or_invalid):
        assert is_valid_url(dangerous_or_invalid) is False

    @pytest.mark.parametrize(
        "internal_target",
        [
            "http://localhost:8080",
            "http://127.0.0.1/",
            "http://127.0.0.1:3000/api",
            "http://[::1]/",
            "http://169.254.169.254/latest/meta-data/",
            "http://10.0.0.1/admin",
            "http://192.168.1.1/router",
            "http://172.16.0.5/",
            "http://internal.corp/",
            "http://server.local/",
        ],
    )
    def test_ssrf_and_private_network_targets_detected(self, internal_target):
        assert is_private_or_internal_host(internal_target) is True

    def test_public_domains_are_not_flagged_as_internal(self):
        assert is_private_or_internal_host("https://google.com") is False
        assert is_private_or_internal_host("https://github.com/login") is False

    def test_virustotal_client_blocks_outbound_ssrf_requests(self):
        """VirusTotalClient must never query VirusTotal for private/internal IPs."""
        res = run(VirusTotalClient.analyze_url("http://127.0.0.1:8000/secret"))
        assert res["available"] is True
        assert res["found"] is False
        assert res.get("is_internal") is True
        assert "internal or private" in res.get("reason", "")

    def test_punycode_and_non_standard_ports_detected(self):
        assert contains_punycode("https://xn--pple-43d.com") is True
        assert contains_punycode("https://apple.com") is False

        assert has_non_standard_port("https://example.com:8443") is True
        assert has_non_standard_port("https://example.com:443") is False
        assert has_non_standard_port("http://example.com:80") is False

    def test_phishing_keywords_detection(self):
        keywords = detect_keywords("http://secure-login-verify-account.com")
        assert "login" in keywords
        assert "verify" in keywords
        assert "account" in keywords
        assert "secure" in keywords

    def test_brand_keywords_do_not_flag_legitimate_root_domains(self):
        """Legitimate brand domains should not be penalized simply for their own brand name."""
        assert "google" not in detect_keywords("https://google.com")
        assert "google" not in detect_keywords("https://google.com/search?q=test")
        assert "google" not in detect_keywords("https://www.google.com")
        assert "google" not in detect_keywords("https://google.co.uk")
        assert "apple" not in detect_keywords("https://apple.com")
        assert "apple" not in detect_keywords("https://www.apple.com/iphone")
        assert "netflix" not in detect_keywords("https://netflix.com")
        assert "paypal" not in detect_keywords("https://paypal.com")

    def test_brand_keywords_flag_deceptive_subdomains(self):
        """Deceptive subdomains impersonating brands on another domain must be flagged."""
        keywords = detect_keywords("https://google.security-login.xyz")
        assert "google" in keywords
        assert any(k in keywords for k in ("login", "security"))

        apple_kw = detect_keywords("https://apple.support-verify.org")
        assert "apple" in apple_kw

    def test_brand_keywords_flag_when_in_paths_of_unrelated_domains(self):
        """Phishing URLs hosting brand-impersonation paths on unrelated domains must be flagged."""
        keywords = detect_keywords("https://phishing-portal.com/google/signin")
        assert "google" in keywords
        assert "signin" in keywords

        paypal_kw = detect_keywords("https://fake-invoice-center.net/paypal/payment")
        assert "paypal" in paypal_kw
        assert "payment" in paypal_kw

    def test_brand_keywords_flag_spoofed_domain_names(self):
        """Lookalike and spoofed domains containing brand names must be flagged."""
        keywords = detect_keywords("https://google-security-update.com")
        assert "google" in keywords

    def test_risk_calculation_penalizes_ssrf_and_punycode(self):
        score, level, recs = calculate_url_risk(
            https=True,
            contains_ip_address=False,
            keywords=["login"],
            length=30,
            subdomains=1,
            is_private_or_internal=True,
            is_punycode=True,
        )
        # Should be penalized heavily for SSRF risk and Punycode
        assert score < 60
        assert any("internal or private" in r for r in recs)
        assert any("Punycode" in r for r in recs)


# ===========================================================================
# 3. Threat Intelligence Status Distinctions
# ===========================================================================

class TestThreatIntelligenceStatus:

    def test_distinguishes_malicious(self):
        agg = ThreatAggregator.aggregate(
            local_score=90,
            vt_result={"available": True, "found": True, "malicious": 5, "suspicious": 0, "harmless": 10},
        )
        assert agg["threat_status"] == "malicious"
        assert agg["final_score"] < 90

    def test_distinguishes_suspicious(self):
        agg = ThreatAggregator.aggregate(
            local_score=90,
            vt_result={"available": True, "found": True, "malicious": 0, "suspicious": 3, "harmless": 12},
        )
        assert agg["threat_status"] == "suspicious"
        assert agg["final_score"] < 90

    def test_distinguishes_clean(self):
        agg = ThreatAggregator.aggregate(
            local_score=95,
            vt_result={"available": True, "found": True, "malicious": 0, "suspicious": 0, "harmless": 45},
        )
        assert agg["threat_status"] == "clean"
        assert any("No known threat intelligence detections" in r for r in agg["reasons"])

    def test_distinguishes_inconclusive_for_unseen_urls(self):
        agg = ThreatAggregator.aggregate(
            local_score=95,
            vt_result={"available": True, "found": False, "malicious": 0, "suspicious": 0, "harmless": 0},
        )
        assert agg["threat_status"] == "inconclusive"
        assert any("inconclusive" in r for r in agg["reasons"])

    def test_distinguishes_unavailable_when_vt_fails(self):
        agg = ThreatAggregator.aggregate(
            local_score=95,
            vt_result={
                "available": False,
                "found": False,
                "malicious": 0,
                "suspicious": 0,
                "reason": "VirusTotal rejected the API key.",
            },
        )
        assert agg["threat_status"] == "unavailable"
        assert any("rejected the API key" in r for r in agg["reasons"])


# ===========================================================================
# 4. Orchestration & Resilience
# ===========================================================================

class TestOrchestratorEdgeCasesAndResilience:

    def test_malformed_llm_json_classification_falls_back_gracefully(self, monkeypatch):
        """If the LLM returns garbage or non-JSON, fallback must be deterministic."""
        class _GarbageLLM:
            def chat(self, *args, **kwargs):
                return "Not a json response: 404 error"

        from app.services.llm.provider_factory import ProviderFactory
        monkeypatch.setattr(ProviderFactory, "get_provider", staticmethod(lambda: _GarbageLLM()))

        # Query without rule keywords to trigger LLM classification path
        decision = IntentRouter.classify("Evaluate general enterprise infrastructure posture", allow_llm=True)
        assert decision.source == "default"
        assert isinstance(decision.intent, Intent)


    def test_orchestrator_handles_missing_tool_gracefully(self, db_session, user_factory):
        """ToolContext with unregistered intent should not raise an unhandled exception."""
        from app.agents.orchestrator import CyberGPTOrchestrator
        from app.agents.router import RoutingDecision

        user = user_factory()
        dummy_decision = RoutingDecision(
            intent=Intent.GENERAL_CONVERSATION, # Not in TOOL_REGISTRY
            confidence=0.5,
            source="rule",
            reason="test",
        )
        res = run(
            CyberGPTOrchestrator._tool(
                decision=dummy_decision,
                question="test",
                db=db_session,
                user_id=user.id,
                conversation_id=1,
            )
        )
        assert res["tool_ok"] is False
        assert "No tool handler" in res["answer"]

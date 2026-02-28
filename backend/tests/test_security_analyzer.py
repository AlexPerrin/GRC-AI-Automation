"""
Unit tests for services/security/analyzer.py.

All LLM and ChromaDB calls are mocked — no network or on-disk state required.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from services.security.analyzer import (
    SECURITY_RETRIEVAL_QUERIES,
    ControlFinding,
    SecurityAnalysisResult,
    SecurityAnalyzer,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_domain_response(
    *,
    domain: str = "access_control",
    framework: str = "NIST CSF",
    control_id: str = "PR.AC",
    status: str = "met",
    risk_score: int = 1,
    overall_risk: str = "low",
    recommendation: str = "approve",
) -> dict:
    return {
        "control_findings": [
            {
                "domain": domain,
                "framework": framework,
                "control_id": control_id,
                "status": status,
                "finding": "Control is fully implemented.",
                "evidence": "Vendor states MFA is enforced for all privileged accounts.",
                "risk_score": risk_score,
            }
        ],
        "overall_risk": overall_risk,
        "recommendation": recommendation,
        "summary": f"Domain looks {overall_risk}.",
        "conditions": [],
    }


@pytest.fixture
def mock_llm():
    llm = MagicMock()
    llm.complete_with_json_output = AsyncMock(return_value=_make_domain_response())
    return llm


@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    retriever.retrieve = MagicMock(return_value="Sample KB context chunk.")
    return retriever


@pytest.fixture
def analyzer(mock_llm, mock_retriever):
    return SecurityAnalyzer(llm=mock_llm, retriever=mock_retriever)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestSecurityAnalyzerReturnType:
    async def test_returns_security_analysis_result_instance(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        assert isinstance(result, SecurityAnalysisResult)

    async def test_all_required_fields_present(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        assert hasattr(result, "control_findings")
        assert hasattr(result, "overall_risk")
        assert hasattr(result, "recommendation")
        assert hasattr(result, "summary")
        assert hasattr(result, "conditions")
        assert hasattr(result, "risk_score")

    async def test_findings_are_control_finding_instances(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        assert len(result.control_findings) > 0
        for finding in result.control_findings:
            assert isinstance(finding, ControlFinding)

    async def test_to_dict_is_json_serializable(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        dumped = json.dumps(result.to_dict())
        parsed = json.loads(dumped)
        assert parsed["overall_risk"] == "low"
        assert isinstance(parsed["control_findings"], list)
        assert "risk_score" in parsed


class TestSecurityAnalyzerCallCounts:
    async def test_llm_called_once_per_domain(self, analyzer, mock_llm):
        await analyzer.analyze(vendor_id=1, doc_id=42)
        assert mock_llm.complete_with_json_output.call_count == len(SECURITY_RETRIEVAL_QUERIES)

    async def test_retriever_called_for_kb_security_and_vendor_collection(
        self, analyzer, mock_retriever
    ):
        vendor_id = 7
        doc_id = 3
        await analyzer.analyze(vendor_id=vendor_id, doc_id=doc_id)

        collections_called = {c.args[1] for c in mock_retriever.retrieve.call_args_list}
        assert "kb_security" in collections_called
        assert f"vendor_{vendor_id}_SECURITY_{doc_id}" in collections_called


class TestSecurityAnalyzerEdgeCases:
    async def test_missing_vendor_collection_returns_result_gracefully(self, mock_llm):
        retriever = MagicMock()

        def _side_effect(query, collection, n=5):
            if collection == "kb_security":
                return "KB context."
            raise Exception("collection not found")

        retriever.retrieve = MagicMock(side_effect=_side_effect)
        analyzer = SecurityAnalyzer(llm=mock_llm, retriever=retriever)

        result = await analyzer.analyze(vendor_id=1, doc_id=99)
        assert isinstance(result, SecurityAnalysisResult)

    async def test_json_decode_error_propagates(self, mock_retriever):
        import json as _json

        llm = MagicMock()
        llm.complete_with_json_output = AsyncMock(
            side_effect=_json.JSONDecodeError("bad json", "", 0)
        )
        analyzer = SecurityAnalyzer(llm=llm, retriever=mock_retriever)

        with pytest.raises(_json.JSONDecodeError):
            await analyzer.analyze(vendor_id=1, doc_id=1)

    async def test_worst_case_risk_aggregation(self, mock_retriever):
        """5 low domains + 1 critical domain -> overall_risk == critical, recommendation == reject."""
        call_count = 0

        async def _varying_response(system, user):
            nonlocal call_count
            call_count += 1
            if call_count == 4:
                return _make_domain_response(overall_risk="critical", recommendation="reject", risk_score=5)
            return _make_domain_response(overall_risk="low", recommendation="approve", risk_score=1)

        llm = MagicMock()
        llm.complete_with_json_output = AsyncMock(side_effect=_varying_response)
        analyzer = SecurityAnalyzer(llm=llm, retriever=mock_retriever)

        result = await analyzer.analyze(vendor_id=1, doc_id=1)
        assert result.overall_risk == "critical"
        assert result.recommendation == "reject"

    async def test_risk_score_is_mean_of_findings(self, mock_retriever):
        """risk_score on result should be the mean of all control finding risk_scores."""
        responses = [
            _make_domain_response(risk_score=2),
            _make_domain_response(risk_score=4),
            _make_domain_response(risk_score=2),
            _make_domain_response(risk_score=4),
            _make_domain_response(risk_score=2),
            _make_domain_response(risk_score=4),
        ]
        llm = MagicMock()
        llm.complete_with_json_output = AsyncMock(side_effect=responses)
        analyzer = SecurityAnalyzer(llm=llm, retriever=mock_retriever)

        result = await analyzer.analyze(vendor_id=1, doc_id=1)
        assert result.risk_score == 3.0

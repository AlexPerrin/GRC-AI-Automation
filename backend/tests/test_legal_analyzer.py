"""
Unit tests for services/legal/analyzer.py.

All LLM and ChromaDB calls are mocked — no network or on-disk state required.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, call, patch

from services.legal.analyzer import (
    LEGAL_RETRIEVAL_QUERIES,
    LegalAnalysisResult,
    LegalAnalyzer,
    RegulationFinding,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_domain_response(
    *,
    regulation: str = "GDPR",
    article: str = "Art. 5",
    status: str = "compliant",
    overall_risk: str = "low",
    recommendation: str = "approve",
) -> dict:
    return {
        "regulation_findings": [
            {
                "regulation": regulation,
                "article": article,
                "status": status,
                "finding": "Vendor meets requirements.",
                "evidence": "Data is processed lawfully.",
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
    llm.complete_with_json_output = AsyncMock(
        return_value=_make_domain_response()
    )
    return llm


@pytest.fixture
def mock_retriever():
    retriever = MagicMock()
    retriever.retrieve = MagicMock(return_value="Sample KB context chunk.")
    return retriever


@pytest.fixture
def analyzer(mock_llm, mock_retriever):
    return LegalAnalyzer(llm=mock_llm, retriever=mock_retriever)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLegalAnalyzerReturnType:
    async def test_returns_legal_analysis_result_instance(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        assert isinstance(result, LegalAnalysisResult)

    async def test_all_required_fields_present(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        assert hasattr(result, "regulation_findings")
        assert hasattr(result, "overall_risk")
        assert hasattr(result, "recommendation")
        assert hasattr(result, "summary")
        assert hasattr(result, "conditions")

    async def test_findings_are_regulation_finding_instances(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        assert len(result.regulation_findings) > 0
        for finding in result.regulation_findings:
            assert isinstance(finding, RegulationFinding)

    async def test_to_dict_is_json_serializable(self, analyzer):
        result = await analyzer.analyze(vendor_id=1, doc_id=42)
        dumped = json.dumps(result.to_dict())
        parsed = json.loads(dumped)
        assert parsed["overall_risk"] == "low"
        assert isinstance(parsed["regulation_findings"], list)


class TestLegalAnalyzerCallCounts:
    async def test_llm_called_once_per_domain(self, analyzer, mock_llm):
        await analyzer.analyze(vendor_id=1, doc_id=42)
        assert mock_llm.complete_with_json_output.call_count == len(LEGAL_RETRIEVAL_QUERIES)

    async def test_retriever_called_for_kb_legal_and_vendor_collection(
        self, analyzer, mock_retriever
    ):
        vendor_id = 5
        doc_id = 10
        await analyzer.analyze(vendor_id=vendor_id, doc_id=doc_id)

        all_calls = mock_retriever.retrieve.call_args_list
        collections_called = {c.args[1] for c in all_calls}

        assert "kb_legal" in collections_called
        assert f"vendor_{vendor_id}_LEGAL_{doc_id}" in collections_called


class TestLegalAnalyzerEdgeCases:
    async def test_missing_vendor_collection_returns_result_gracefully(
        self, mock_llm
    ):
        """Retriever raises for vendor collection; analyzer should still return a result."""
        retriever = MagicMock()

        def _retrieve_side_effect(query, collection, n=5):
            if collection == "kb_legal":
                return "KB context."
            raise Exception("collection not found")

        retriever.retrieve = MagicMock(side_effect=_retrieve_side_effect)
        analyzer = LegalAnalyzer(llm=mock_llm, retriever=retriever)

        result = await analyzer.analyze(vendor_id=1, doc_id=99)
        assert isinstance(result, LegalAnalysisResult)

    async def test_json_decode_error_propagates(self, mock_retriever):
        """JSONDecodeError from LLM should propagate out of analyze()."""
        import json as _json

        llm = MagicMock()
        llm.complete_with_json_output = AsyncMock(
            side_effect=_json.JSONDecodeError("bad json", "", 0)
        )
        analyzer = LegalAnalyzer(llm=llm, retriever=mock_retriever)

        with pytest.raises(_json.JSONDecodeError):
            await analyzer.analyze(vendor_id=1, doc_id=1)

    async def test_worst_case_risk_aggregation(self, mock_retriever):
        """5 domains return low + 1 returns critical → overall_risk == critical, recommendation == reject."""
        call_count = 0

        async def _varying_response(system, user):
            nonlocal call_count
            call_count += 1
            if call_count == 3:  # third domain is the bad one
                return _make_domain_response(
                    overall_risk="critical",
                    recommendation="reject",
                )
            return _make_domain_response(overall_risk="low", recommendation="approve")

        llm = MagicMock()
        llm.complete_with_json_output = AsyncMock(side_effect=_varying_response)
        analyzer = LegalAnalyzer(llm=llm, retriever=mock_retriever)

        result = await analyzer.analyze(vendor_id=1, doc_id=1)
        assert result.overall_risk == "critical"
        assert result.recommendation == "reject"

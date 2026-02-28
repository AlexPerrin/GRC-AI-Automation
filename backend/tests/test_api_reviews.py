"""
API integration tests for review endpoints.

Uses the client fixture (FastAPI TestClient with in-memory SQLite).
WorkflowService.trigger_legal_review is patched as AsyncMock for the trigger tests
so no real LLM or ChromaDB calls are made.
"""
import pytest
from unittest.mock import AsyncMock, patch

from core.models import (
    DocumentStage,
    Review,
    ReviewStatus,
    ReviewType,
    Vendor,
    VendorStatus,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_vendor(db_session, status=VendorStatus.USE_CASE_APPROVED):
    v = Vendor(name="Test Vendor", status=status)
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


def _create_review(db_session, vendor_id, stage=DocumentStage.LEGAL, review_type=ReviewType.AI_ANALYSIS):
    r = Review(
        vendor_id=vendor_id,
        stage=stage,
        review_type=review_type,
        status=ReviewStatus.PENDING,
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


def _make_complete_review_dict(review):
    """Return a dict that looks like ReviewRead but with COMPLETE status."""
    return {
        "id": review.id,
        "vendor_id": review.vendor_id,
        "stage": review.stage.value,
        "review_type": review.review_type.value,
        "status": ReviewStatus.COMPLETE.value,
        "ai_output": {"overall_risk": "low", "recommendation": "approve"},
        "form_input": None,
        "triggered_at": review.triggered_at.isoformat(),
        "completed_at": None,
    }


# ---------------------------------------------------------------------------
# Tests — GET endpoints
# ---------------------------------------------------------------------------

class TestListReviews:
    def test_empty_list(self, client, db_session):
        vendor = _create_vendor(db_session)
        resp = client.get(f"/vendors/{vendor.id}/reviews")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_returns_reviews_for_vendor(self, client, db_session):
        vendor = _create_vendor(db_session)
        review = _create_review(db_session, vendor.id)

        resp = client.get(f"/vendors/{vendor.id}/reviews")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id"] == review.id
        assert data[0]["stage"] == "LEGAL"
        assert data[0]["review_type"] == "AI_ANALYSIS"

    def test_vendor_not_found_returns_404(self, client):
        resp = client.get("/vendors/99999/reviews")
        assert resp.status_code == 404


class TestGetReview:
    def test_get_existing_review(self, client, db_session):
        vendor = _create_vendor(db_session)
        review = _create_review(db_session, vendor.id)

        resp = client.get(f"/reviews/{review.id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == review.id

    def test_get_not_found_returns_404(self, client):
        resp = client.get("/reviews/99999")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Tests — POST /reviews/{id}/trigger
# ---------------------------------------------------------------------------

class TestTriggerAiReview:
    def test_trigger_not_found_returns_404(self, client):
        resp = client.post("/reviews/99999/trigger", params={"doc_id": 1})
        assert resp.status_code == 404

    def test_trigger_human_form_review_type_returns_400(self, client, db_session):
        vendor = _create_vendor(db_session)
        review = _create_review(
            db_session, vendor.id, review_type=ReviewType.HUMAN_FORM
        )
        resp = client.post(f"/reviews/{review.id}/trigger", params={"doc_id": 1})
        assert resp.status_code == 400

    def test_trigger_legal_stage_mocked_success_returns_200(self, client, db_session):
        vendor = _create_vendor(db_session)
        review = _create_review(
            db_session, vendor.id, stage=DocumentStage.LEGAL, review_type=ReviewType.AI_ANALYSIS
        )

        # Build a mock ORM Review with COMPLETE status to return from the service
        mock_review = Review(
            id=review.id,
            vendor_id=review.vendor_id,
            stage=DocumentStage.LEGAL,
            review_type=ReviewType.AI_ANALYSIS,
            status=ReviewStatus.COMPLETE,
            ai_output={"overall_risk": "low", "recommendation": "approve"},
            triggered_at=review.triggered_at,
            completed_at=None,
        )

        with patch(
            "api.routes.reviews.WorkflowService.trigger_legal_review",
            new=AsyncMock(return_value=mock_review),
        ):
            resp = client.post(f"/reviews/{review.id}/trigger", params={"doc_id": 1})

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETE"

    def test_trigger_security_stage_nda_gate_returns_403(self, client, db_session):
        """Vendor not in SECURITY_REVIEW (NDA not confirmed) -> 403."""
        vendor = _create_vendor(db_session, status=VendorStatus.LEGAL_APPROVED)
        review = _create_review(
            db_session, vendor.id, stage=DocumentStage.SECURITY, review_type=ReviewType.AI_ANALYSIS
        )
        resp = client.post(f"/reviews/{review.id}/trigger", params={"doc_id": 1})
        assert resp.status_code == 403

    def test_trigger_security_stage_mocked_success_returns_200(self, client, db_session):
        vendor = _create_vendor(db_session, status=VendorStatus.SECURITY_REVIEW)
        review = _create_review(
            db_session, vendor.id, stage=DocumentStage.SECURITY, review_type=ReviewType.AI_ANALYSIS
        )

        mock_review = Review(
            id=review.id,
            vendor_id=review.vendor_id,
            stage=DocumentStage.SECURITY,
            review_type=ReviewType.AI_ANALYSIS,
            status=ReviewStatus.COMPLETE,
            ai_output={"overall_risk": "medium", "recommendation": "approve_with_conditions", "risk_score": 2.5},
            triggered_at=review.triggered_at,
            completed_at=None,
        )

        with patch(
            "api.routes.reviews.WorkflowService.trigger_security_review",
            new=AsyncMock(return_value=mock_review),
        ):
            resp = client.post(f"/reviews/{review.id}/trigger", params={"doc_id": 1})

        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETE"

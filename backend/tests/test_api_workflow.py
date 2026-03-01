"""
Integration tests for the complete vendor onboarding workflow endpoints.
Uses client fixture with TestClient — no LLM or ChromaDB needed.
"""
import pytest

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

def _use_case_body(**kwargs):
    base = dict(
        use_case_description="Automate procurement",
        business_justification="Saves time",
        data_types_involved=["PII"],
        estimated_users=10,
        alternatives_considered="None",
        reviewer_name="Alice",
        recommendation="PROCEED",
    )
    base.update(kwargs)
    return base


def _financial_body(**kwargs):
    base = dict(
        financial_documents_reviewed=["balance_sheet"],
        concentration_risk_flag=False,
        financial_stability_assessment="STABLE",
        reviewer_name="Bob",
        recommendation="ACCEPTABLE",
    )
    base.update(kwargs)
    return base


def _seed_vendor(db_session, status=VendorStatus.INTAKE, name="Test Vendor"):
    v = Vendor(name=name, status=status)
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


def _seed_review(db_session, vendor_id, stage, review_type=ReviewType.HUMAN_FORM,
                 status=ReviewStatus.PENDING):
    r = Review(
        vendor_id=vendor_id,
        stage=stage,
        review_type=review_type,
        status=status,
    )
    db_session.add(r)
    db_session.commit()
    db_session.refresh(r)
    return r


# ---------------------------------------------------------------------------
# TestStartIntake
# ---------------------------------------------------------------------------

class TestStartIntake:
    def test_intake_vendor_advances_to_use_case_review(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.INTAKE)
        resp = client.post(f"/vendors/{v.id}/start-intake")
        assert resp.status_code == 200
        assert resp.json()["status"] == "USE_CASE_REVIEW"

    def test_non_intake_vendor_returns_400(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        resp = client.post(f"/vendors/{v.id}/start-intake")
        assert resp.status_code == 400

    def test_not_found_returns_404(self, client):
        resp = client.post("/vendors/99999/start-intake")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestSubmitForm
# ---------------------------------------------------------------------------

class TestSubmitForm:
    def test_use_case_form_returns_200_and_complete(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.USE_CASE_REVIEW)
        r = _seed_review(db_session, v.id, DocumentStage.USE_CASE)
        resp = client.post(f"/reviews/{r.id}/submit-form", json=_use_case_body())
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETE"

    def test_financial_form_returns_200_and_complete(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.FINANCIAL_REVIEW)
        r = _seed_review(db_session, v.id, DocumentStage.FINANCIAL)
        resp = client.post(f"/reviews/{r.id}/submit-form", json=_financial_body())
        assert resp.status_code == 200
        assert resp.json()["status"] == "COMPLETE"

    def test_legal_stage_review_returns_400(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _seed_review(db_session, v.id, DocumentStage.LEGAL)
        resp = client.post(f"/reviews/{r.id}/submit-form", json={"dummy": "data"})
        assert resp.status_code == 400

    def test_review_not_found_returns_404(self, client):
        resp = client.post("/reviews/99999/submit-form", json=_use_case_body())
        assert resp.status_code == 404

    def test_invalid_body_returns_422(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.USE_CASE_REVIEW)
        r = _seed_review(db_session, v.id, DocumentStage.USE_CASE)
        resp = client.post(f"/reviews/{r.id}/submit-form", json={"bad": "data"})
        assert resp.status_code == 422

    def test_proceed_advances_vendor_to_use_case_approved(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.USE_CASE_REVIEW)
        r = _seed_review(db_session, v.id, DocumentStage.USE_CASE)
        client.post(f"/reviews/{r.id}/submit-form", json=_use_case_body(recommendation="PROCEED"))
        vendor_resp = client.get(f"/vendors/{v.id}")
        assert vendor_resp.json()["status"] == "USE_CASE_APPROVED"


# ---------------------------------------------------------------------------
# TestStartFinancialReview
# ---------------------------------------------------------------------------

class TestStartFinancialReview:
    def test_security_approved_vendor_advances_to_financial_review(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.SECURITY_APPROVED)
        resp = client.post(f"/vendors/{v.id}/start-financial-review")
        assert resp.status_code == 200
        assert resp.json()["status"] == "FINANCIAL_REVIEW"

    def test_wrong_status_returns_400(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.LEGAL_APPROVED)
        resp = client.post(f"/vendors/{v.id}/start-financial-review")
        assert resp.status_code == 400

    def test_not_found_returns_404(self, client):
        resp = client.post("/vendors/99999/start-financial-review")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestCompleteOnboarding
# ---------------------------------------------------------------------------

class TestCompleteOnboarding:
    def test_financial_approved_advances_to_onboarded(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.FINANCIAL_APPROVED)
        resp = client.post(f"/vendors/{v.id}/complete-onboarding")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ONBOARDED"

    def test_wrong_status_returns_400(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.SECURITY_APPROVED)
        resp = client.post(f"/vendors/{v.id}/complete-onboarding")
        assert resp.status_code == 400

    def test_not_found_returns_404(self, client):
        resp = client.post("/vendors/99999/complete-onboarding")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestRejectVendor
# ---------------------------------------------------------------------------

class TestRejectVendor:
    def test_any_vendor_can_be_rejected(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        resp = client.post(f"/vendors/{v.id}/reject", params={"rationale": "Not a fit"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "REJECTED"

    def test_not_found_returns_404(self, client):
        resp = client.post("/vendors/99999/reject", params={"rationale": "Gone"})
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# TestDecisionWithStateTransition
# ---------------------------------------------------------------------------

class TestDecisionWithStateTransition:
    def _approve_payload(self, actor="reviewer"):
        return {"actor": actor, "action": "APPROVE", "rationale": "Looks good"}

    def test_legal_approve_decision_advances_vendor_to_legal_approved(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _seed_review(
            db_session, v.id, DocumentStage.LEGAL,
            review_type=ReviewType.AI_ANALYSIS, status=ReviewStatus.COMPLETE,
        )
        resp = client.post(f"/reviews/{r.id}/decisions", json=self._approve_payload())
        assert resp.status_code == 201
        vendor_resp = client.get(f"/vendors/{v.id}")
        assert vendor_resp.json()["status"] == "LEGAL_APPROVED"

    def test_security_approve_decision_advances_vendor_to_security_approved(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.SECURITY_REVIEW)
        r = _seed_review(
            db_session, v.id, DocumentStage.SECURITY,
            review_type=ReviewType.AI_ANALYSIS, status=ReviewStatus.COMPLETE,
        )
        resp = client.post(f"/reviews/{r.id}/decisions", json=self._approve_payload())
        assert resp.status_code == 201
        vendor_resp = client.get(f"/vendors/{v.id}")
        assert vendor_resp.json()["status"] == "SECURITY_APPROVED"

    def test_decision_on_pending_review_returns_400(self, client, db_session):
        v = _seed_vendor(db_session, status=VendorStatus.LEGAL_REVIEW)
        r = _seed_review(
            db_session, v.id, DocumentStage.LEGAL,
            review_type=ReviewType.AI_ANALYSIS, status=ReviewStatus.PENDING,
        )
        resp = client.post(f"/reviews/{r.id}/decisions", json=self._approve_payload())
        assert resp.status_code == 400

    def test_decision_on_nonexistent_review_returns_404(self, client):
        resp = client.post("/reviews/99999/decisions", json=self._approve_payload())
        assert resp.status_code == 404

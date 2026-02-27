"""
Unit tests for core/models.py — ORM model creation and relationships.
"""
import pytest
from core.models import (
    AuditLog,
    Decision,
    DecisionAction,
    Document,
    DocumentStage,
    Review,
    ReviewStatus,
    ReviewType,
    Vendor,
    VendorStatus,
)


class TestVendorStatus:
    def test_all_states_present(self):
        expected = {
            "INTAKE", "USE_CASE_REVIEW", "USE_CASE_APPROVED",
            "LEGAL_REVIEW", "LEGAL_APPROVED", "NDA_PENDING",
            "SECURITY_REVIEW", "SECURITY_APPROVED",
            "FINANCIAL_REVIEW", "FINANCIAL_APPROVED",
            "ONBOARDED", "REJECTED",
        }
        assert {s.value for s in VendorStatus} == expected

    def test_vendor_status_is_string(self):
        assert isinstance(VendorStatus.INTAKE, str)
        assert VendorStatus.INTAKE == "INTAKE"


class TestVendorModel:
    def test_create_vendor_minimal(self, db_session):
        vendor = Vendor(name="Acme Corp")
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)

        assert vendor.id is not None
        assert vendor.name == "Acme Corp"
        assert vendor.status == VendorStatus.INTAKE
        assert vendor.created_at is not None

    def test_create_vendor_full(self, db_session):
        vendor = Vendor(
            name="Beta Ltd",
            website="https://beta.example.com",
            description="A test vendor",
        )
        db_session.add(vendor)
        db_session.commit()
        db_session.refresh(vendor)

        assert vendor.website == "https://beta.example.com"
        assert vendor.description == "A test vendor"

    def test_vendor_status_can_be_updated(self, db_session):
        vendor = Vendor(name="Gamma Inc")
        db_session.add(vendor)
        db_session.commit()

        vendor.status = VendorStatus.USE_CASE_REVIEW
        db_session.commit()
        db_session.refresh(vendor)

        assert vendor.status == VendorStatus.USE_CASE_REVIEW


class TestDocumentModel:
    def test_create_document_linked_to_vendor(self, db_session):
        vendor = Vendor(name="Doc Vendor")
        db_session.add(vendor)
        db_session.commit()

        doc = Document(
            vendor_id=vendor.id,
            stage=DocumentStage.LEGAL,
            doc_type="privacy_policy",
            filename="privacy.pdf",
        )
        db_session.add(doc)
        db_session.commit()
        db_session.refresh(doc)

        assert doc.id is not None
        assert doc.vendor_id == vendor.id
        assert doc.stage == DocumentStage.LEGAL

    def test_vendor_documents_relationship(self, db_session):
        vendor = Vendor(name="Rel Vendor")
        db_session.add(vendor)
        db_session.commit()

        for name in ("soc2.pdf", "dpa.pdf"):
            doc = Document(
                vendor_id=vendor.id,
                stage=DocumentStage.SECURITY,
                doc_type="soc2",
                filename=name,
            )
            db_session.add(doc)
        db_session.commit()
        db_session.refresh(vendor)

        assert len(vendor.documents) == 2

    def test_cascade_delete_removes_documents(self, db_session):
        vendor = Vendor(name="Cascade Vendor")
        db_session.add(vendor)
        db_session.commit()

        doc = Document(
            vendor_id=vendor.id,
            stage=DocumentStage.USE_CASE,
            doc_type="overview",
            filename="overview.docx",
        )
        db_session.add(doc)
        db_session.commit()

        db_session.delete(vendor)
        db_session.commit()

        remaining = db_session.query(Document).filter_by(vendor_id=vendor.id).all()
        assert remaining == []


class TestReviewModel:
    def test_create_review(self, db_session):
        vendor = Vendor(name="Review Vendor")
        db_session.add(vendor)
        db_session.commit()

        review = Review(
            vendor_id=vendor.id,
            stage=DocumentStage.LEGAL,
            review_type=ReviewType.AI_ANALYSIS,
        )
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        assert review.id is not None
        assert review.status == ReviewStatus.PENDING
        assert review.triggered_at is not None
        assert review.completed_at is None


class TestDecisionModel:
    def test_create_decision_linked_to_review(self, db_session):
        vendor = Vendor(name="Decision Vendor")
        db_session.add(vendor)
        db_session.commit()

        review = Review(
            vendor_id=vendor.id,
            stage=DocumentStage.SECURITY,
            review_type=ReviewType.HUMAN_FORM,
        )
        db_session.add(review)
        db_session.commit()

        decision = Decision(
            review_id=review.id,
            actor="compliance@example.com",
            action=DecisionAction.APPROVE,
            rationale="All checks passed.",
        )
        db_session.add(decision)
        db_session.commit()
        db_session.refresh(decision)

        assert decision.id is not None
        assert decision.action == DecisionAction.APPROVE
        assert decision.decided_at is not None


class TestAuditLogModel:
    def test_create_audit_log(self, db_session):
        vendor = Vendor(name="Audit Vendor")
        db_session.add(vendor)
        db_session.commit()

        log = AuditLog(
            vendor_id=vendor.id,
            event_type="STATUS_CHANGE",
            actor="system",
            payload={"from": "INTAKE", "to": "USE_CASE_REVIEW"},
        )
        db_session.add(log)
        db_session.commit()
        db_session.refresh(log)

        assert log.id is not None
        assert log.payload["from"] == "INTAKE"

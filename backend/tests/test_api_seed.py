"""
Tests for the POST /dev/seed endpoint.

Strategy:
- Patch VectorStore.upsert_chunks so tests don't need a live ChromaDB instance.
- Verify DB state directly via db_session after the call.
"""
import pytest
from unittest.mock import MagicMock, patch

from core.models import Document, Review, ReviewStatus, ReviewType, Vendor, VendorStatus, DocumentStage


@pytest.fixture
def seed_client(client):
    """Client with VectorStore.upsert_chunks stubbed out."""
    with patch(
        "api.routes.dev.VectorStore.upsert_chunks",
        return_value=None,
    ):
        yield client


class TestSeedEndpoint:
    def test_seed_returns_200(self, seed_client):
        resp = seed_client.post("/dev/seed")
        assert resp.status_code == 200

    def test_seed_response_shape(self, seed_client):
        resp = seed_client.post("/dev/seed")
        data = resp.json()
        assert "message" in data
        assert "vendors" in data
        assert isinstance(data["vendors"], list)

    def test_seed_creates_three_vendors(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        count = db_session.query(Vendor).count()
        assert count == 3

    def test_seed_vendor_names(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        names = {v.name for v in db_session.query(Vendor).all()}
        assert "Acme Analytics Inc." in names
        assert "DataFlow Inc." in names
        assert "SecureVault Ltd." in names

    def test_seed_creates_one_document_per_vendor(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        count = db_session.query(Document).count()
        assert count == 3

    def test_seed_documents_have_raw_text(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        docs = db_session.query(Document).all()
        for doc in docs:
            assert doc.raw_text and len(doc.raw_text) > 100

    def test_seed_documents_have_chroma_collection_id(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        docs = db_session.query(Document).all()
        for doc in docs:
            assert doc.chroma_collection_id is not None
            assert doc.chroma_collection_id.startswith("vendor_")

    def test_seed_creates_four_reviews_per_vendor(self, seed_client, db_session):
        """Each vendor gets USE_CASE + LEGAL + SECURITY + FINANCIAL reviews (4 × 3 = 12)."""
        seed_client.post("/dev/seed")
        count = db_session.query(Review).count()
        assert count == 12

    def test_seed_reviews_are_pending(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        reviews = db_session.query(Review).all()
        for review in reviews:
            assert review.status == ReviewStatus.PENDING

    def test_seed_all_vendors_have_legal_review(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        legal_reviews = (
            db_session.query(Review)
            .filter(Review.stage == DocumentStage.LEGAL)
            .all()
        )
        assert len(legal_reviews) == 3
        for review in legal_reviews:
            assert review.review_type == ReviewType.AI_ANALYSIS

    def test_seed_all_vendors_have_security_review(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        security_reviews = (
            db_session.query(Review)
            .filter(Review.stage == DocumentStage.SECURITY)
            .all()
        )
        assert len(security_reviews) == 3
        for review in security_reviews:
            assert review.review_type == ReviewType.AI_ANALYSIS

    def test_seed_all_vendors_have_financial_review(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        financial_reviews = (
            db_session.query(Review)
            .filter(Review.stage == DocumentStage.FINANCIAL)
            .all()
        )
        assert len(financial_reviews) == 3
        for review in financial_reviews:
            assert review.review_type == ReviewType.AI_ANALYSIS

    def test_seed_response_includes_all_ids(self, seed_client, db_session):
        resp = seed_client.post("/dev/seed")
        vendors_in_response = resp.json()["vendors"]
        assert len(vendors_in_response) == 3
        for entry in vendors_in_response:
            assert "id" in entry
            assert "name" in entry
            assert "document_id" in entry
            assert "review_id" in entry

    def test_seed_upsert_called_once_per_vendor(self, client):
        with patch(
            "api.routes.dev.VectorStore.upsert_chunks",
            return_value=None,
        ) as mock_upsert:
            client.post("/dev/seed")
            assert mock_upsert.call_count == 3

    def test_seed_is_idempotent(self, seed_client, db_session):
        """Second call should wipe state and recreate — still exactly 3 vendors."""
        seed_client.post("/dev/seed")
        seed_client.post("/dev/seed")
        assert db_session.query(Vendor).count() == 3
        assert db_session.query(Document).count() == 3
        assert db_session.query(Review).count() == 12

    def test_seed_idempotent_response_message(self, seed_client):
        resp1 = seed_client.post("/dev/seed")
        resp2 = seed_client.post("/dev/seed")
        assert resp1.json()["message"] == resp2.json()["message"]

    def test_seed_collection_name_format(self, seed_client, db_session):
        """Collection IDs follow vendor_{id}_{stage}_{doc_id} convention."""
        seed_client.post("/dev/seed")
        docs = db_session.query(Document).all()
        for doc in docs:
            expected = f"vendor_{doc.vendor_id}_{doc.stage.value}_{doc.id}"
            assert doc.chroma_collection_id == expected

    def test_seed_vendors_start_in_use_case_review_status(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        for vendor in db_session.query(Vendor).all():
            assert vendor.status == VendorStatus.USE_CASE_REVIEW

    def test_seed_each_vendor_has_use_case_review(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        use_case_reviews = (
            db_session.query(Review)
            .filter(Review.stage == DocumentStage.USE_CASE)
            .all()
        )
        assert len(use_case_reviews) == 3
        for review in use_case_reviews:
            assert review.review_type == ReviewType.HUMAN_FORM
            assert review.status == ReviewStatus.PENDING

    def test_seed_response_review_id_is_use_case_review(self, seed_client, db_session):
        """review_id in the response should point to the USE_CASE review."""
        resp = seed_client.post("/dev/seed")
        for entry in resp.json()["vendors"]:
            review = db_session.query(Review).filter(Review.id == entry["review_id"]).first()
            assert review is not None
            assert review.stage == DocumentStage.USE_CASE

    def test_seed_dataflow_is_legal_stage(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        dataflow = db_session.query(Vendor).filter(Vendor.name == "DataFlow Inc.").first()
        assert dataflow is not None
        doc = db_session.query(Document).filter(Document.vendor_id == dataflow.id).first()
        assert doc.stage == DocumentStage.LEGAL

    def test_seed_securevault_is_security_stage(self, seed_client, db_session):
        seed_client.post("/dev/seed")
        sv = db_session.query(Vendor).filter(Vendor.name == "SecureVault Ltd.").first()
        assert sv is not None
        doc = db_session.query(Document).filter(Document.vendor_id == sv.id).first()
        assert doc.stage == DocumentStage.SECURITY

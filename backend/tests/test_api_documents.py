"""
Integration tests for document upload / list / get API endpoints.
DocumentExtractor, DocumentChunker, and VectorStore are mocked so no real
file parsing or ChromaDB calls occur.
"""
import io
import pytest
from unittest.mock import MagicMock, patch

from core.models import Vendor


@pytest.fixture
def vendor(db_session):
    v = Vendor(name="Test Vendor", website="https://example.com")
    db_session.add(v)
    db_session.commit()
    db_session.refresh(v)
    return v


def _make_upload_file(content: bytes = b"dummy content", filename: str = "test.txt"):
    return ("file", (filename, io.BytesIO(content), "text/plain"))


class TestUploadDocument:
    def test_upload_returns_201(self, client, vendor):
        with (
            patch("api.routes.documents.DocumentExtractor") as mock_ext_cls,
            patch("api.routes.documents.DocumentChunker") as mock_chunker_cls,
            patch("api.routes.documents.VectorStore") as mock_vs_cls,
        ):
            mock_ext_cls.return_value.extract.return_value = "extracted text"
            mock_chunker_cls.return_value.chunk.return_value = []
            mock_vs_cls.return_value.upsert_chunks.return_value = None

            response = client.post(
                f"/vendors/{vendor.id}/documents",
                params={"stage": "LEGAL", "doc_type": "nda"},
                files=[_make_upload_file()],
            )

        assert response.status_code == 201

    def test_upload_invokes_extractor_and_stores_document(self, client, vendor, db_session):
        with (
            patch("api.routes.documents.DocumentExtractor") as mock_ext_cls,
            patch("api.routes.documents.DocumentChunker") as mock_chunker_cls,
            patch("api.routes.documents.VectorStore") as mock_vs_cls,
        ):
            mock_ext_cls.return_value.extract.return_value = "hello world"
            mock_chunker_cls.return_value.chunk.return_value = []
            mock_vs_cls.return_value.upsert_chunks.return_value = None

            response = client.post(
                f"/vendors/{vendor.id}/documents",
                params={"stage": "SECURITY", "doc_type": "soc2"},
                files=[_make_upload_file()],
            )

        assert response.status_code == 201
        # raw_text is persisted in the DB but not exposed in DocumentRead
        from core.models import Document
        doc = db_session.query(Document).filter(Document.id == response.json()["id"]).first()
        assert doc.raw_text == "hello world"

    def test_upload_sets_chroma_collection_id(self, client, vendor):
        with (
            patch("api.routes.documents.DocumentExtractor") as mock_ext_cls,
            patch("api.routes.documents.DocumentChunker") as mock_chunker_cls,
            patch("api.routes.documents.VectorStore") as mock_vs_cls,
        ):
            mock_ext_cls.return_value.extract.return_value = "text"
            mock_chunker_cls.return_value.chunk.return_value = []
            mock_vs_cls.return_value.upsert_chunks.return_value = None

            response = client.post(
                f"/vendors/{vendor.id}/documents",
                params={"stage": "LEGAL", "doc_type": "nda"},
                files=[_make_upload_file()],
            )

        data = response.json()
        assert data["chroma_collection_id"] is not None
        assert str(vendor.id) in data["chroma_collection_id"]

    def test_upload_vendor_not_found_returns_404(self, client):
        with (
            patch("api.routes.documents.DocumentExtractor") as mock_ext_cls,
            patch("api.routes.documents.DocumentChunker") as mock_chunker_cls,
            patch("api.routes.documents.VectorStore") as mock_vs_cls,
        ):
            mock_ext_cls.return_value.extract.return_value = "text"
            mock_chunker_cls.return_value.chunk.return_value = []

            response = client.post(
                "/vendors/9999/documents",
                params={"stage": "LEGAL", "doc_type": "nda"},
                files=[_make_upload_file()],
            )

        assert response.status_code == 404

    def test_upload_calls_extractor(self, client, vendor):
        with (
            patch("api.routes.documents.DocumentExtractor") as mock_ext_cls,
            patch("api.routes.documents.DocumentChunker") as mock_chunker_cls,
            patch("api.routes.documents.VectorStore") as mock_vs_cls,
        ):
            mock_ext = mock_ext_cls.return_value
            mock_ext.extract.return_value = "content"
            mock_chunker_cls.return_value.chunk.return_value = []
            mock_vs_cls.return_value.upsert_chunks.return_value = None

            client.post(
                f"/vendors/{vendor.id}/documents",
                params={"stage": "LEGAL", "doc_type": "nda"},
                files=[_make_upload_file(filename="doc.txt")],
            )

        mock_ext.extract.assert_called_once()


class TestListDocuments:
    def test_list_returns_empty_for_new_vendor(self, client, vendor):
        response = client.get(f"/vendors/{vendor.id}/documents")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_returns_uploaded_documents(self, client, vendor):
        with (
            patch("api.routes.documents.DocumentExtractor") as mock_ext_cls,
            patch("api.routes.documents.DocumentChunker") as mock_chunker_cls,
            patch("api.routes.documents.VectorStore") as mock_vs_cls,
        ):
            mock_ext_cls.return_value.extract.return_value = "text"
            mock_chunker_cls.return_value.chunk.return_value = []
            mock_vs_cls.return_value.upsert_chunks.return_value = None

            client.post(
                f"/vendors/{vendor.id}/documents",
                params={"stage": "LEGAL", "doc_type": "nda"},
                files=[_make_upload_file()],
            )

        response = client.get(f"/vendors/{vendor.id}/documents")
        assert response.status_code == 200
        assert len(response.json()) == 1

    def test_list_vendor_not_found_returns_404(self, client):
        response = client.get("/vendors/9999/documents")
        assert response.status_code == 404


class TestGetDocument:
    def test_get_existing_document(self, client, vendor):
        with (
            patch("api.routes.documents.DocumentExtractor") as mock_ext_cls,
            patch("api.routes.documents.DocumentChunker") as mock_chunker_cls,
            patch("api.routes.documents.VectorStore") as mock_vs_cls,
        ):
            mock_ext_cls.return_value.extract.return_value = "text"
            mock_chunker_cls.return_value.chunk.return_value = []
            mock_vs_cls.return_value.upsert_chunks.return_value = None

            upload_resp = client.post(
                f"/vendors/{vendor.id}/documents",
                params={"stage": "LEGAL", "doc_type": "nda"},
                files=[_make_upload_file()],
            )
        doc_id = upload_resp.json()["id"]
        response = client.get(f"/documents/{doc_id}")
        assert response.status_code == 200
        assert response.json()["id"] == doc_id

    def test_get_nonexistent_document_returns_404(self, client):
        response = client.get("/documents/99999")
        assert response.status_code == 404

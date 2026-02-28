"""
Unit tests for services/document/chunker.py.
Uses real RecursiveCharacterTextSplitter but with controlled inputs.
"""
import pytest

from services.document.chunker import Chunk, DocumentChunker


@pytest.fixture
def chunker():
    return DocumentChunker(chunk_size=100, overlap=10)


class TestDocumentChunker:
    def test_chunks_long_text(self, chunker):
        long_text = "word " * 200  # ~1000 chars
        chunks = chunker.chunk(long_text, {"doc_id": 1})
        assert len(chunks) > 1

    def test_returns_chunk_objects(self, chunker):
        chunks = chunker.chunk("Hello world", {"doc_id": 1})
        assert all(isinstance(c, Chunk) for c in chunks)

    def test_preserves_metadata(self, chunker):
        meta = {"doc_id": 42, "vendor_id": 7, "stage": "LEGAL"}
        chunks = chunker.chunk("Some text", meta)
        for c in chunks:
            assert c.metadata["doc_id"] == 42
            assert c.metadata["vendor_id"] == 7
            assert c.metadata["stage"] == "LEGAL"

    def test_chunk_index_increments(self, chunker):
        long_text = "word " * 200
        chunks = chunker.chunk(long_text, {})
        indices = [c.metadata["chunk_index"] for c in chunks]
        assert indices == list(range(len(chunks)))

    def test_short_text_produces_one_chunk(self, chunker):
        chunks = chunker.chunk("Short text.", {})
        assert len(chunks) <= 1

    def test_empty_text_produces_no_chunks(self, chunker):
        chunks = chunker.chunk("", {})
        assert len(chunks) == 0

    def test_chunk_text_is_string(self, chunker):
        chunks = chunker.chunk("Hello world this is a test document.", {})
        for c in chunks:
            assert isinstance(c.text, str)
            assert len(c.text) > 0

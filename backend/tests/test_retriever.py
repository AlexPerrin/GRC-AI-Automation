"""
Unit tests for services/rag/retriever.py.
VectorStore is mocked.
"""
import pytest
from unittest.mock import MagicMock

from services.rag.retriever import Retriever


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.query.return_value = ["chunk one", "chunk two", "chunk three"]
    return store


@pytest.fixture
def retriever(mock_store):
    return Retriever(store=mock_store)


class TestRetriever:
    def test_retrieve_joins_with_separator(self, retriever, mock_store):
        result = retriever.retrieve("query", "kb_legal", n=3)
        assert result == "chunk one\n---\nchunk two\n---\nchunk three"

    def test_passes_n_to_store(self, retriever, mock_store):
        retriever.retrieve("query", "kb_legal", n=7)
        mock_store.query.assert_called_once_with("kb_legal", "query", 7)

    def test_passes_collection_to_store(self, retriever, mock_store):
        retriever.retrieve("find something", "kb_security", n=5)
        args = mock_store.query.call_args
        assert args[0][0] == "kb_security"

    def test_single_chunk_no_separator(self, retriever, mock_store):
        mock_store.query.return_value = ["only chunk"]
        result = retriever.retrieve("q", "col", n=1)
        assert result == "only chunk"
        assert "---" not in result

    def test_empty_result_returns_empty_string(self, retriever, mock_store):
        mock_store.query.return_value = []
        result = retriever.retrieve("q", "col", n=5)
        assert result == ""

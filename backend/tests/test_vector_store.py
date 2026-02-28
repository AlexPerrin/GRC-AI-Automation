"""
Unit tests for services/rag/store.py.
chromadb.PersistentClient and the module-level Embedder are mocked.
"""
import pytest
from unittest.mock import MagicMock, patch

from services.document.chunker import Chunk
from services.rag.store import VectorStore


def _make_mock_collection(name="test_col"):
    col = MagicMock()
    col.name = name
    return col


def _make_mock_client(collections=None):
    client = MagicMock()
    col = _make_mock_collection()
    client.get_or_create_collection.return_value = col
    client.list_collections.return_value = [
        MagicMock(name=c) for c in (collections or [])
    ]
    return client, col


@pytest.fixture
def mock_embedder():
    embedder = MagicMock()
    embedder.embed.return_value = [[0.1, 0.2, 0.3]]
    return embedder


class TestVectorStoreUpsert:
    def test_calls_get_or_create_collection(self, mock_embedder):
        client, col = _make_mock_client()
        store = VectorStore()
        store._client = client
        chunks = [Chunk(text="chunk text", metadata={"doc_id": 1})]

        with patch("services.rag.store._embedder", mock_embedder):
            store.upsert_chunks("my_collection", chunks)

        client.get_or_create_collection.assert_called_once_with("my_collection")

    def test_upsert_called_with_correct_ids(self, mock_embedder):
        client, col = _make_mock_client()
        store = VectorStore()
        store._client = client
        chunks = [
            Chunk(text="a", metadata={}),
            Chunk(text="b", metadata={}),
        ]
        mock_embedder.embed.return_value = [[0.1, 0.2], [0.3, 0.4]]

        with patch("services.rag.store._embedder", mock_embedder):
            store.upsert_chunks("col", chunks)

        call_kwargs = col.upsert.call_args.kwargs
        assert call_kwargs["ids"] == ["col_0", "col_1"]

    def test_upsert_called_with_documents(self, mock_embedder):
        client, col = _make_mock_client()
        store = VectorStore()
        store._client = client
        chunks = [Chunk(text="hello world", metadata={"x": 1})]

        with patch("services.rag.store._embedder", mock_embedder):
            store.upsert_chunks("col", chunks)

        call_kwargs = col.upsert.call_args.kwargs
        assert "hello world" in call_kwargs["documents"]


class TestVectorStoreQuery:
    def test_query_returns_documents(self, mock_embedder):
        client = MagicMock()
        col = MagicMock()
        client.get_or_create_collection.return_value = col
        col.query.return_value = {"documents": [["chunk 1", "chunk 2"]]}
        mock_embedder.embed.return_value = [[0.1, 0.2]]

        store = VectorStore()
        store._client = client

        with patch("services.rag.store._embedder", mock_embedder):
            result = store.query("col", "find something", n_results=2)

        assert result == ["chunk 1", "chunk 2"]

    def test_query_passes_n_results(self, mock_embedder):
        client = MagicMock()
        col = MagicMock()
        client.get_or_create_collection.return_value = col
        col.query.return_value = {"documents": [["x"]]}
        mock_embedder.embed.return_value = [[0.1]]

        store = VectorStore()
        store._client = client

        with patch("services.rag.store._embedder", mock_embedder):
            store.query("col", "query text", n_results=7)

        col.query.assert_called_once()
        assert col.query.call_args.kwargs["n_results"] == 7


class TestVectorStoreCollectionExists:
    def test_returns_true_when_exists(self):
        client = MagicMock()
        # ChromaDB v0.6.0+: list_collections returns strings, not objects
        client.list_collections.return_value = ["kb_legal", "kb_security"]

        store = VectorStore()
        store._client = client

        assert store.collection_exists("kb_legal") is True

    def test_returns_false_when_absent(self):
        client = MagicMock()
        client.list_collections.return_value = []

        store = VectorStore()
        store._client = client

        assert store.collection_exists("kb_legal") is False

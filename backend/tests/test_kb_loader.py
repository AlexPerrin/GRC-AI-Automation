"""
Unit tests for services/knowledge_base/loader.py.
VectorStore is mocked; no real ChromaDB or embeddings.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from services.knowledge_base.loader import KnowledgeBaseLoader


@pytest.fixture
def mock_store():
    store = MagicMock()
    store.collection_exists.return_value = False
    return store


class TestKnowledgeBaseLoader:
    async def test_seeds_when_collections_absent(self, mock_store):
        loader = KnowledgeBaseLoader(store=mock_store)
        await loader.seed_if_empty()
        assert mock_store.upsert_chunks.call_count == 2

    async def test_skips_when_both_collections_exist(self, mock_store):
        mock_store.collection_exists.return_value = True
        loader = KnowledgeBaseLoader(store=mock_store)
        await loader.seed_if_empty()
        mock_store.upsert_chunks.assert_not_called()

    async def test_seeds_only_missing_collection(self, mock_store):
        def exists_side_effect(name):
            return name == "kb_legal"

        mock_store.collection_exists.side_effect = exists_side_effect
        loader = KnowledgeBaseLoader(store=mock_store)
        await loader.seed_if_empty()
        # Only kb_security should be seeded
        assert mock_store.upsert_chunks.call_count == 1
        call_args = mock_store.upsert_chunks.call_args
        assert call_args[0][0] == "kb_security"

    async def test_chunks_passed_to_upsert_have_entry_id(self, mock_store):
        loader = KnowledgeBaseLoader(store=mock_store)
        await loader.seed_if_empty()
        # Check that chunks for at least one collection have entry_id in metadata
        for call in mock_store.upsert_chunks.call_args_list:
            chunks = call[0][1]
            assert len(chunks) > 0
            assert "entry_id" in chunks[0].metadata

    async def test_upsert_called_with_correct_collection_names(self, mock_store):
        loader = KnowledgeBaseLoader(store=mock_store)
        await loader.seed_if_empty()
        call_names = [call[0][0] for call in mock_store.upsert_chunks.call_args_list]
        assert "kb_legal" in call_names
        assert "kb_security" in call_names

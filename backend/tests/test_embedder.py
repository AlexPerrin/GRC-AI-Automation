"""
Unit tests for services/rag/embedder.py.
SentenceTransformer is mocked so no model download is required.
"""
import pytest
from unittest.mock import MagicMock, patch

from services.rag.embedder import Embedder


class _FakeArray:
    """Minimal stand-in for numpy array with .tolist()."""
    def __init__(self, data):
        self._data = data
    def tolist(self):
        return self._data


@pytest.fixture
def mock_st_model():
    """Return a mock SentenceTransformer that produces fixed-shape embeddings."""
    model = MagicMock()
    model.encode.return_value = _FakeArray([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    return model


class TestEmbedder:
    def test_returns_list_of_lists(self, mock_st_model):
        with patch("sentence_transformers.SentenceTransformer", return_value=mock_st_model):
            embedder = Embedder()
            result = embedder.embed(["text one", "text two"])

        assert isinstance(result, list)
        assert all(isinstance(v, list) for v in result)

    def test_correct_shape(self, mock_st_model):
        with patch("sentence_transformers.SentenceTransformer", return_value=mock_st_model):
            embedder = Embedder()
            result = embedder.embed(["text one", "text two"])

        assert len(result) == 2
        assert len(result[0]) == 3

    def test_lazy_loads_model_on_first_call(self, mock_st_model):
        with patch("sentence_transformers.SentenceTransformer", return_value=mock_st_model) as mock_cls:
            embedder = Embedder()
            assert embedder._model is None
            embedder.embed(["hello"])
            mock_cls.assert_called_once()
            assert embedder._model is not None

    def test_model_not_reloaded_on_second_call(self, mock_st_model):
        with patch("sentence_transformers.SentenceTransformer", return_value=mock_st_model) as mock_cls:
            embedder = Embedder()
            embedder.embed(["first call"])
            embedder.embed(["second call"])
            mock_cls.assert_called_once()

    def test_normalize_flag_passed(self, mock_st_model):
        with patch("sentence_transformers.SentenceTransformer", return_value=mock_st_model):
            embedder = Embedder()
            embedder.embed(["text"])

        mock_st_model.encode.assert_called_once_with(["text"], normalize_embeddings=True)

    def test_single_text_returns_single_embedding(self):
        mock_model = MagicMock()
        mock_model.encode.return_value = _FakeArray([[0.1, 0.2]])
        with patch("sentence_transformers.SentenceTransformer", return_value=mock_model):
            embedder = Embedder()
            result = embedder.embed(["single"])
        assert len(result) == 1

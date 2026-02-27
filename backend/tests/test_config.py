"""
Unit tests for core/config.py — Settings properties.
"""
from core.config import Settings


def test_llm_model_string_anthropic():
    s = Settings(LLM_PROVIDER="anthropic", LLM_MODEL="claude-sonnet-4-6", LLM_PROVIDER_API_KEY="k")
    assert s.llm_model_string == "anthropic/claude-sonnet-4-6"


def test_llm_model_string_openai():
    s = Settings(LLM_PROVIDER="openai", LLM_MODEL="gpt-4o", LLM_PROVIDER_API_KEY="k")
    assert s.llm_model_string == "openai/gpt-4o"


def test_llm_model_string_openrouter():
    s = Settings(
        LLM_PROVIDER="openrouter",
        LLM_MODEL="anthropic/claude-sonnet-4-6",
        LLM_PROVIDER_API_KEY="k",
    )
    assert s.llm_model_string == "openrouter/anthropic/claude-sonnet-4-6"


def test_chroma_use_server_false_when_host_empty():
    s = Settings(CHROMA_HOST="", LLM_PROVIDER_API_KEY="k")
    assert s.chroma_use_server is False


def test_chroma_use_server_true_when_host_set():
    s = Settings(CHROMA_HOST="chromadb", LLM_PROVIDER_API_KEY="k")
    assert s.chroma_use_server is True


def test_default_embedding_model():
    s = Settings(LLM_PROVIDER_API_KEY="k")
    assert s.EMBEDDING_MODEL == "all-MiniLM-L6-v2"

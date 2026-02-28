from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./vendor_onboarding.db"

    # LLM provider selection: "anthropic" | "openai" | "openrouter"
    LLM_PROVIDER: str = "anthropic"
    # Model ID passed to litellm after the provider prefix.
    # For OpenRouter, use the full routed model path, e.g. "anthropic/claude-sonnet-4-6"
    LLM_MODEL: str = "claude-sonnet-4-6"

    LLM_PROVIDER_API_KEY: str = ""

    # ChromaDB — used only in local dev (embedded mode).
    # In Docker, CHROMA_HOST/PORT override these and HttpClient is used instead.
    CHROMA_PERSIST_DIR: str = "./chroma_data"
    CHROMA_HOST: str = ""       # set to "chromadb" in docker-compose
    CHROMA_PORT: int = 8000

    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    @property
    def chroma_use_server(self) -> bool:
        """True when a remote ChromaDB server is configured."""
        return bool(self.CHROMA_HOST)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def llm_model_string(self) -> str:
        """
        Return the litellm model string for the configured provider.
        Examples:
          anthropic  + claude-sonnet-4-6             → anthropic/claude-sonnet-4-6
          openai     + gpt-4o                         → openai/gpt-4o
          openrouter + anthropic/claude-sonnet-4-6   → openrouter/anthropic/claude-sonnet-4-6
        """
        return f"{self.LLM_PROVIDER}/{self.LLM_MODEL}"


settings = Settings()

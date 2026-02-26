from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./vendor_onboarding.db"

    # LLM provider selection: "anthropic" | "openai" | "openrouter"
    LLM_PROVIDER: str = "anthropic"
    # Model ID passed to litellm after the provider prefix.
    # For OpenRouter, use the full routed model path, e.g. "anthropic/claude-sonnet-4-6"
    LLM_MODEL: str = "claude-sonnet-4-6"

    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    CHROMA_PERSIST_DIR: str = "./chroma_data"
    EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def llm_api_key(self) -> str:
        """Return the API key for the configured LLM provider."""
        return {
            "anthropic": self.ANTHROPIC_API_KEY,
            "openai": self.OPENAI_API_KEY,
            "openrouter": self.OPENROUTER_API_KEY,
        }.get(self.LLM_PROVIDER, "")

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

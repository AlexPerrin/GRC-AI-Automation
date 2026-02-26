"""
LLM client — litellm wrapper with structured JSON output support.
Stub for Day 1; fully implemented in Day 2.
"""
import json
import re

from core.config import settings


class LLMClient:
    """
    Thin wrapper around litellm providing a consistent interface for all
    AI analysis modules.  Uses the provider and model configured in Settings.
    """

    def __init__(self):
        self.model = f"{settings.LLM_PROVIDER}/{settings.LLM_MODEL}"

    async def complete(self, system: str, user: str) -> str:
        """Return a raw string completion. Implemented Day 2."""
        raise NotImplementedError

    async def complete_with_json_output(self, system: str, user: str) -> dict:
        """
        Return a parsed JSON dict.  Strips markdown fences and retries once
        on decode failure.  Implemented Day 2.
        """
        raise NotImplementedError

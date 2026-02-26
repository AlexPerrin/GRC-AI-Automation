"""
LLM client — litellm wrapper with structured JSON output support.

Supports three providers via the LLM_PROVIDER / LLM_MODEL env vars:
  anthropic  — direct Anthropic API
  openai     — direct OpenAI API
  openrouter — OpenRouter aggregator (access 200+ models with one key)

litellm model string format:
  "{LLM_PROVIDER}/{LLM_MODEL}"
  e.g. "openrouter/anthropic/claude-sonnet-4-6"
       "anthropic/claude-sonnet-4-6"
       "openai/gpt-4o"
"""
import json
import re

import litellm

from core.config import settings

# Suppress litellm's verbose startup banner
litellm.suppress_debug_info = True


class LLMClient:
    """
    Thin wrapper around litellm providing a consistent async interface for all
    AI analysis modules. Provider and model are resolved from Settings so
    switching providers requires only an env var change.
    """

    def __init__(self):
        self.model = settings.llm_model_string
        self._api_key = settings.llm_api_key

    async def complete(self, system: str, user: str) -> str:
        """Return a raw string completion from the configured model."""
        response = await litellm.acompletion(
            model=self.model,
            api_key=self._api_key,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content

    async def complete_with_json_output(self, system: str, user: str) -> dict:
        """
        Return a parsed JSON dict.

        Models sometimes wrap JSON in markdown fences (```json ... ```).
        This method strips fences and retries the parse once before raising.
        """
        raw = await self.complete(system, user)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
            return json.loads(cleaned)

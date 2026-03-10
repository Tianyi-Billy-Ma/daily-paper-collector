import json
import logging
import os
import re

import anthropic

from src.llm.base import LLMProvider


class ClaudeProvider(LLMProvider):
    def __init__(self, config: dict):
        self.logger = logging.getLogger(__name__)
        api_key_env = config.get("api_key_env", "ANTHROPIC_API_KEY")
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"Environment variable '{api_key_env}' is not set")

        # Support custom base_url from config or environment
        base_url = config.get("base_url") or os.environ.get("ANTHROPIC_BASE_URL")
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url
            self.logger.info(f"Using custom Anthropic base_url: {base_url}")

        self.client = anthropic.AsyncAnthropic(**client_kwargs)
        self.model = config.get("model", "claude-sonnet-4-5-20250929")

    async def complete(self, prompt: str, system: str = "") -> str:
        kwargs = {
            "model": self.model,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            kwargs["system"] = system

        response = await self.client.messages.create(**kwargs)
        return response.content[0].text

    async def complete_json(self, prompt: str, system: str = "") -> dict:
        system_msg = (
            f"{system}\nRespond with valid JSON only."
            if system
            else "Respond with valid JSON only."
        )
        text = await self.complete(prompt, system=system_msg)

        # Strip markdown code fences if present
        stripped = re.sub(r"^```(?:json)?\s*\n?", "", text.strip())
        stripped = re.sub(r"\n?```\s*$", "", stripped)

        try:
            return json.loads(stripped)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM response is not valid JSON: {e}") from e

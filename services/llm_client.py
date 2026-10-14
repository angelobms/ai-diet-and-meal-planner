"""Single gateway for all LLM requests (OpenAI-compatible chat completions)."""
import json
import os
from typing import Any, Dict

import httpx
from dotenv import load_dotenv

load_dotenv()


class LLMClient:
    """Thin client that sends a prompt and returns the model's JSON reply.

    Uses Groq when GROQ_API_KEY is set, otherwise OpenAI with OPENAI_API_KEY.
    Keys are read from the environment (loaded from .env).
    """

    def __init__(self):
        if os.getenv("GROQ_API_KEY"):
            self.api_key = os.getenv("GROQ_API_KEY")
            self.api_url = "https://api.groq.com/openai/v1/chat/completions"
            self.model = "llama-3.1-8b-instant"
        else:
            self.api_key = os.getenv("OPENAI_API_KEY")
            self.api_url = "https://api.openai.com/v1/chat/completions"
            self.model = "gpt-4o-mini"

    def call_model_json(self, prompt: str) -> Dict[str, Any]:
        """Send `prompt` in JSON mode and return the parsed response object.

        Raises:
            RuntimeError: no API key is configured.
            httpx.HTTPError: the API request failed or returned an error status.
            ValueError: the model reply is not valid JSON.
        """
        if not self.api_key:
            raise RuntimeError("Set GROQ_API_KEY or OPENAI_API_KEY in .env")
        response = httpx.post(
            self.api_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "response_format": {"type": "json_object"},
                "temperature": 0,
            },
            timeout=30,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

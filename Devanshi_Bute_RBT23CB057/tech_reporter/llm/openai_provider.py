"""OpenAI and OpenAI-compatible (Ollama, Groq, vLLM) LLM Provider."""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import Optional
from tech_reporter.llm.base import LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI compatible LLM provider."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        base_url: str = "https://api.openai.com/v1"
    ):
        self.api_key = api_key or "no-key-required"
        self.model = model
        self.base_url = base_url.rstrip("/")

    @property
    def model_name(self) -> str:
        return self.model

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        temperature: float = 0.7,
        json_mode: bool = False
    ) -> str:
        # Check if official openai SDK is installed first
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key, base_url=self.base_url)
            messages = []
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})
            messages.append({"role": "user", "content": prompt})

            kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content or ""
        except ImportError:
            pass  # Fall back to zero-dependency direct HTTP REST request

        url = f"{self.base_url}/chat/completions"
        messages = []
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}

        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        req = urllib.request.Request(url, data=data, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                choices = result.get("choices", [])
                if not choices:
                    raise RuntimeError(f"OpenAI API returned no choices: {result}")
                return choices[0].get("message", {}).get("content", "")
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"OpenAI API HTTP Error {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"OpenAI API invocation failed: {str(e)}") from e

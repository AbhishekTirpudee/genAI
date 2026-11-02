"""Gemini API Provider supporting both direct HTTP REST API and official SDK."""

from __future__ import annotations
import json
import urllib.request
import urllib.error
from typing import Optional
from tech_reporter.llm.base import LLMProvider


class GeminiProvider(LLMProvider):
    """Google Gemini LLM provider."""

    def __init__(self, api_key: str, model: str = "gemini-2.5-flash"):
        self.api_key = api_key
        self.model = model
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY is required for GeminiProvider.")

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
        # Check if official SDK is installed first
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            generation_config = {
                "temperature": temperature,
            }
            if json_mode:
                generation_config["response_mime_type"] = "application/json"

            model_inst = genai.GenerativeModel(
                model_name=self.model,
                system_instruction=system_instruction
            )
            resp = model_inst.generate_content(
                prompt,
                generation_config=generation_config
            )
            if resp.text:
                return resp.text
        except ImportError:
            pass  # Fall back to zero-dependency direct HTTP REST request

        # Zero-dependency direct REST request to Google Generative Language API
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"

        payload: dict = {
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": temperature,
            }
        }

        if system_instruction:
            payload["systemInstruction"] = {
                "parts": [{"text": system_instruction}]
            }

        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                result = json.loads(response.read().decode("utf-8"))
                candidates = result.get("candidates", [])
                if not candidates:
                    raise RuntimeError(f"Gemini API returned no candidates: {result}")
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    raise RuntimeError(f"Gemini API returned empty parts: {result}")
                return "".join(p.get("text", "") for p in parts)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Gemini API HTTP Error {e.code}: {err_body}") from e
        except Exception as e:
            raise RuntimeError(f"Gemini API invocation failed: {str(e)}") from e

"""
LLM Connector for College Result Analysis Agent.
Supports Google Gemini, OpenAI, or Groq via standard urllib without extra external dependencies.
Gracefully falls back to the built-in offline semantic rule engine if no API key is provided.
"""

import os
import json
import urllib.request
import urllib.error

class LLMConnector:
    def __init__(self, api_key=None, provider=None):
        self.api_key = api_key or os.environ.get('GEMINI_API_KEY') or os.environ.get('OPENAI_API_KEY') or os.environ.get('GROQ_API_KEY')
        
        if not provider:
            if os.environ.get('GEMINI_API_KEY'):
                self.provider = 'gemini'
            elif os.environ.get('GROQ_API_KEY'):
                self.provider = 'groq'
            elif os.environ.get('OPENAI_API_KEY'):
                self.provider = 'openai'
            elif self.api_key and self.api_key.startswith('AIza'):
                self.provider = 'gemini'
            elif self.api_key and self.api_key.startswith('gsk_'):
                self.provider = 'groq'
            else:
                self.provider = 'openai' if self.api_key else None
        else:
            self.provider = provider.lower()

    def is_available(self) -> bool:
        return bool(self.api_key and self.provider)

    def query_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Sends request to configured LLM API provider."""
        if not self.is_available():
            raise ValueError("No LLM API Key configured.")

        if self.provider == 'gemini':
            return self._call_gemini(prompt, system_prompt)
        elif self.provider in ('openai', 'groq'):
            return self._call_openai_compatible(prompt, system_prompt)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")

    def _call_gemini(self, prompt: str, system_prompt: str) -> str:
        # Gemini 1.5 Flash or Gemini 2.0 Flash endpoint
        model = "gemini-2.0-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
        
        contents = []
        if system_prompt:
            contents.append({"role": "user", "parts": [{"text": f"System Instructions: {system_prompt}"}]})
            contents.append({"role": "model", "parts": [{"text": "Understood. I will strictly follow these instructions."}]})
        contents.append({"role": "user", "parts": [{"text": prompt}]})

        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 1000
            }
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                candidates = result.get('candidates', [])
                if candidates and 'content' in candidates[0]:
                    parts = candidates[0]['content'].get('parts', [])
                    if parts:
                        return parts[0].get('text', '')
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise RuntimeError(f"Gemini API Error ({e.code}): {err_body}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to Gemini API: {str(e)}")

    def _call_openai_compatible(self, prompt: str, system_prompt: str) -> str:
        if self.provider == 'groq':
            url = "https://api.groq.com/openai/v1/chat/completions"
            model = "llama-3.3-70b-versatile"
        else:
            url = "https://api.openai.com/v1/chat/completions"
            model = "gpt-4o-mini"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.1,
            "max_tokens": 800
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.api_key}'
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                result = json.loads(response.read().decode('utf-8'))
                choices = result.get('choices', [])
                if choices:
                    return choices[0]['message']['content']
                return ""
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8')
            raise RuntimeError(f"{self.provider.upper()} API Error ({e.code}): {err_body}")
        except Exception as e:
            raise RuntimeError(f"Failed to connect to {self.provider.upper()} API: {str(e)}")

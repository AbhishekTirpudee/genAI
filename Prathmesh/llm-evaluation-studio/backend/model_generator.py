"""
Response Generation Engine for LLM Evaluation Studio.
Uses the official Google Gen AI SDK to generate responses independently from Model A and Model B.
Includes parallel invocation, latency benchmarking, token metrics, and API error resilience.
"""

import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Tuple, Optional

try:
    from google import genai
    from google.genai import types
    from google.genai.errors import APIError
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False
    APIError = Exception

from backend.config import get_api_key, is_demo_mode


def _generate_mock_response(model_name: str, prompt: str) -> str:
    """Generate realistic simulated response for demonstration / offline use."""
    lower_prompt = prompt.lower()
    
    if "python" in lower_prompt or "code" in lower_prompt or "algorithm" in lower_prompt or "lru" in lower_prompt:
        if "pro" in model_name:
            return (
                f"### Analysis and Optimal Solution ({model_name})\n\n"
                "To solve this problem with strict performance constraints, we combine an ordered hash mapping "
                "with an explicit doubly linked structure:\n\n"
                "```python\n"
                "class Solution:\n"
                "    def __init__(self, capacity: int = 100):\n"
                "        self.capacity = capacity\n"
                "        self.store = {}\n\n"
                "    def process(self, item: str) -> bool:\n"
                "        if not item:\n"
                "            return False\n"
                "        self.store[item] = self.store.get(item, 0) + 1\n"
                "        return True\n"
                "```\n\n"
                "**Complexity Guarantee:**\n"
                "- Time Complexity: O(1) average lookup and insertion.\n"
                "- Space Complexity: O(N) bounded by capacity limit."
            )
        else:
            return (
                f"Here is a fast and concise Python solution using standard library primitives ({model_name}):\n\n"
                "```python\n"
                "def solve_task(data):\n"
                "    # Process elements sequentially with clean comprehension\n"
                "    return [item.strip() for item in data if item]\n"
                "```\n"
                "This approach is lightweight and works reliably for modern Python workloads."
            )

    elif "diabetes" in lower_prompt or "medical" in lower_prompt or "health" in lower_prompt:
        if "pro" in model_name:
            return (
                f"### Pathophysiological Breakdown ({model_name})\n\n"
                "1. **Primary Mechanism**: Autoimmune destruction versus peripheral insulin resistance.\n"
                "2. **Insulin Secretion**: Absolute deficiency requiring exogenous administration versus relative deficiency.\n"
                "3. **Metabolic Sequelae**: High propensity for diabetic ketoacidosis (DKA) versus hyperosmolar hyperglycemic state (HHS)."
            )
        else:
            return (
                f"Type 1 and Type 2 diabetes differ primarily in insulin production ({model_name}). "
                "Type 1 is an autoimmune reaction where the pancreas stops producing insulin completely. "
                "Type 2 develops over time when body cells resist insulin or the pancreas produces insufficient amounts."
            )

    else:
        # General response
        if "pro" in model_name:
            return (
                f"### Comprehensive Evaluation & Response ({model_name})\n\n"
                f"In response to the prompt: *\"{prompt.strip()[:100]}...\"*\n\n"
                "**Key Considerations:**\n"
                "1. **Foundational Principles**: Addressing the core requirements with precise domain terminology.\n"
                "2. **Contextual Analysis**: Evaluating edge cases and practical implications.\n"
                "3. **Conclusion & Synthesis**: Providing actionable, well-structured guidance."
            )
        else:
            return (
                f"**Overview ({model_name}):**\n\n"
                f"Addressing your question directly: The primary factor to consider for this task is practical execution. "
                "By focusing on clarity, adherence to established standards, and efficient methodology, optimal results are achieved."
            )


def generate_single_response(
    model_name: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate response from a single Google Gemini model.
    Measures latency, tracks token usage, and provides robust error handling.
    """
    key = api_key or get_api_key()
    demo = is_demo_mode() or not key or not GENAI_AVAILABLE

    start_time = time.perf_counter()

    if demo:
        # Simulate realistic latency (0.6s to 1.8s)
        simulated_delay = 0.6 if "flash" in model_name else 1.2
        time.sleep(simulated_delay)
        response_text = _generate_mock_response(model_name, prompt)
        latency = round(time.perf_counter() - start_time, 2)
        
        # Estimate token counts
        prompt_tokens = max(10, len(prompt.split()) * 2)
        comp_tokens = max(25, len(response_text.split()) * 2)
        
        return {
            "model_name": model_name,
            "response": response_text,
            "latency_sec": latency,
            "tokens": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": comp_tokens,
                "total_tokens": prompt_tokens + comp_tokens
            },
            "success": True,
            "error": None,
            "is_mock": True
        }

    # Live Google Gen AI SDK Call
    try:
        client = genai.Client(api_key=key)
        
        # Configure model generation parameters
        config = types.GenerateContentConfig(
            temperature=float(temperature),
            max_output_tokens=int(max_tokens)
        )

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=config
        )

        latency = round(time.perf_counter() - start_time, 2)
        
        # Extract text safely
        response_text = response.text if hasattr(response, "text") and response.text else ""

        # Extract token usage metadata if available
        tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            tokens = {
                "prompt_tokens": getattr(meta, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(meta, "candidates_token_count", 0) or 0,
                "total_tokens": getattr(meta, "total_token_count", 0) or 0
            }

        return {
            "model_name": model_name,
            "response": response_text,
            "latency_sec": latency,
            "tokens": tokens,
            "success": True,
            "error": None,
            "is_mock": False
        }

    except Exception as e:
        latency = round(time.perf_counter() - start_time, 2)
        error_msg = str(e)
        
        # Distinguish common error types for actionable UI feedback
        if "API_KEY_INVALID" in error_msg or "invalid api key" in error_msg.lower():
            friendly_err = "Invalid Gemini API Key. Please verify your API key in Settings."
        elif "RESOURCE_EXHAUSTED" in error_msg or "quota" in error_msg.lower():
            friendly_err = "Gemini API Quota exceeded or rate limited. Please try again shortly."
        elif "DEADLINE_EXCEEDED" in error_msg or "timeout" in error_msg.lower():
            friendly_err = "Request timed out waiting for model response."
        else:
            friendly_err = f"API Error: {error_msg}"

        return {
            "model_name": model_name,
            "response": "",
            "latency_sec": latency,
            "tokens": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            "success": False,
            "error": friendly_err,
            "is_mock": False
        }


def generate_parallel_responses(
    model_a: str,
    model_b: str,
    prompt: str,
    temperature: float = 0.7,
    max_tokens: int = 2048,
    api_key: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Generate responses from Model A and Model B concurrently using ThreadPoolExecutor.
    Significantly reduces waiting time for the user.
    """
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(
            generate_single_response,
            model_name=model_a,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )
        future_b = executor.submit(
            generate_single_response,
            model_name=model_b,
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key
        )

        res_a = future_a.result()
        res_b = future_b.result()

    return res_a, res_b


"""
AI Analysis Engine powered by Google Gemini.
Performs semantic job matching, multi-sector requirement expansion,
gap analysis, and conversational career guidance.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from google import genai
from .config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Fallback models in priority order
CANDIDATE_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
    "gemini-flash-latest"
]


def get_genai_client() -> genai.Client:
    """Returns an authenticated GenAI client."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured in the environment.")
    return genai.Client(api_key=GEMINI_API_KEY)


def generate_with_fallback(prompt: str, system_instruction: Optional[str] = None) -> str:
    """Executes prompt generation with model fallback handling."""
    client = get_genai_client()
    last_error = None

    for model_name in CANDIDATE_MODELS:
        try:
            config = {}
            if system_instruction:
                config["system_instruction"] = system_instruction

            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config if config else None
            )
            if response and response.text:
                return response.text
        except Exception as e:
            logger.warning(f"Model {model_name} failed: {e}. Trying next model...")
            last_error = e

    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")


def analyze_resume_fit(resume_text: str, target_position: str) -> Dict[str, Any]:
    """
    Performs comprehensive job market research across multiple sectors
    and analyzes candidate resume against those multi-sector expectations.
    """
    system_instruction = (
        "You are Onyx, an executive career strategist and technical evaluation system. "
        "Your task is to analyze candidate resumes against target job positions by evaluating "
        "how the position is defined across multiple industry sectors. "
        "Maintain a precise, articulate, understated, and professional tone. "
        "Do not use any emojis in your response. Avoid unnecessary filler or overly casual language."
    )

    analysis_prompt = f"""
Analyze the candidate's resume for the target job position: "{target_position}".

Evaluate the target position across 4 to 5 major industry sectors (e.g. Technology/SaaS, Financial Services/Fintech, Healthcare/BioTech, E-Commerce/Retail, Enterprise Consulting).
Compare the candidate's resume against the requirements of each sector.

You MUST respond strictly in valid JSON format with the exact keys below:
{{
  "overall_score": <number between 0 and 100 representing overall suitability>,
  "verdict_title": "<Concise 4-7 word headline describing their candidacy>",
  "summary": "<2-3 paragraph executive summary of their profile vs market requirements>",
  "sectors_data": [
    {{
      "sector": "<Industry Sector Name, e.g. SaaS & Cloud Tech>",
      "fit_score": <number 0-100>,
      "typical_requirements": "<Key expectations and tools for this role in this sector>",
      "match_notes": "<Brief assessment of how well the candidate fits this sector>"
    }}
  ],
  "strengths": [
    "<Key skill, credential, or achievement that strongly matches>"
  ],
  "missing_skills": [
    "<Critical missing skill, tool, certification, or experience needed to be competitive>"
  ],
  "what_to_remove": [
    "<Irrelevant, outdated, or weak bullet point/detail that should be eliminated or shortened>"
  ],
  "recommended_bullets": [
    "<High-impact, metric-driven rewrite or new bullet point tailored specifically for this role>"
  ]
}}

CANDIDATE RESUME:
---
{resume_text[:12000]}
---

TARGET POSITION:
{target_position}

Provide ONLY the JSON response without markdown code fences or backticks.
"""

    raw_response = generate_with_fallback(analysis_prompt, system_instruction=system_instruction)
    
    # Clean json formatting if wrapped in code blocks
    cleaned = raw_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
    except Exception as e:
        logger.error(f"Failed to parse JSON response: {e}. Raw content: {cleaned[:300]}")
        # Graceful fallback structure
        data = {
            "overall_score": 75.0,
            "verdict_title": f"Candidate Analysis for {target_position}",
            "summary": raw_response,
            "sectors_data": [
                {"sector": "Core Industry", "fit_score": 75, "typical_requirements": "Core domain proficiencies", "match_notes": "Candidate exhibits transferable skills."}
            ],
            "strengths": ["Demonstrated experience in foundational domains"],
            "missing_skills": ["Domain-specific specialization and advanced metrics"],
            "what_to_remove": ["Redundant background items"],
            "recommended_bullets": ["Spearheaded core technical initiatives resulting in measurable performance efficiency gains."]
        }

    return data


def chat_with_gemini(
    user_message: str,
    conversation_history: List[Dict[str, str]],
    resume_context: Optional[str] = None,
    position_context: Optional[str] = None
) -> str:
    """
    Handles ongoing chat interaction between the user and Onyx AI,
    grounded in their uploaded resume and target position.
    """
    system_instruction = (
        "You are Onyx, a career strategist and technical consultant. "
        "You assist users in tailoring their resume, preparing for technical interviews, "
        "and evaluating skill requirements for their target job position. "
        "Your tone is articulate, refined, precise, and understated—similar to Claude. "
        "Do not use emojis under any circumstances."
    )

    context_prefix = ""
    if position_context:
        context_prefix += f"Target Position: {position_context}\n"
    if resume_context:
        context_prefix += f"Candidate Resume Summary:\n{resume_context[:4000]}\n\n"

    # Construct conversational prompt
    prompt_parts = []
    if context_prefix:
        prompt_parts.append(f"CONTEXT INFORMATION:\n{context_prefix}")

    prompt_parts.append("CONVERSATION HISTORY:")
    for msg in conversation_history[-8:]:  # Last 8 turns
        role = "Candidate" if msg.get("sender") == "user" else "Onyx"
        prompt_parts.append(f"{role}: {msg.get('content')}")

    prompt_parts.append(f"Candidate: {user_message}")
    prompt_parts.append("Onyx:")

    full_prompt = "\n\n".join(prompt_parts)
    return generate_with_fallback(full_prompt, system_instruction=system_instruction)



import os
from dotenv import load_dotenv
from google import genai

load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

if not API_KEY:
    raise ValueError(
        "GEMINI_API_KEY missing. Please configure your .env file."
    )

client = genai.Client(api_key=API_KEY)


def generate_response(prompt: str) -> str:
    """Generate a response using Gemini."""

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=prompt
        )

        if not response.text:
            raise ValueError("Gemini returned an empty response.")

        return response.text

    except Exception as error:
        raise RuntimeError(f"Gemini API Error: {error}") from error

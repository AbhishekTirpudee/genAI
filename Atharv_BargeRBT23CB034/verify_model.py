"""
Model Verification Utility for VisionQA.
Checks your Gemini API key and tests active multimodal models against an in-memory sample image.
"""

import os
import io
import sys
from dotenv import load_dotenv
from PIL import Image

# Load environment configuration
load_dotenv()


def run_verification():
    print("=" * 60)
    print(" VisionQA — Gemini Model Verification & Diagnostic Tool")
    print("=" * 60)

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("[ERROR] No GEMINI_API_KEY found in .env file.")
        print("Please add your API key to .env: GEMINI_API_KEY=your_key")
        return

    masked_key = f"{api_key[:4]}••••{api_key[-4:]}" if len(api_key) > 8 else "••••••••"
    print(f"[*] API Key detected: {masked_key}")

    # 1. Initialize client
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        print("[*] Google Gen AI Client initialized successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Google Gen AI Client: {e}")
        return

    # 2. Query available models
    print("\n[*] Querying available models from Google AI API...")
    available_models = []
    try:
        for m in client.models.list():
            actions = getattr(m, "supported_actions", []) or []
            if "generateContent" in actions:
                clean_name = m.name.replace("models/", "")
                available_models.append(clean_name)
        print(f"[OK] Found {len(available_models)} models supporting content generation.")
    except Exception as e:
        print(f"[WARNING] Could not list models: {e}")

    # 3. Create a small in-memory test image
    img = Image.new("RGB", (100, 100), color="dodgerblue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()
    image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")

    # Priority list of models to test
    candidates = [
        "gemini-2.5-flash",
        "gemini-1.5-flash",
        "gemini-2.0-flash",
        "gemini-1.5-pro",
        "gemini-2.5-flash-lite",
        "gemini-flash-latest",
        "gemini-3.8-flash",
    ]

    # Add any detected candidates not already in list
    for m in available_models:
        if "flash" in m and m not in candidates:
            candidates.append(m)

    print("\n[*] Testing multimodal vision capability with candidate models:")
    working_model = None

    for model_name in candidates:
        sys.stdout.write(f"  - Testing '{model_name}'... ")
        sys.stdout.flush()
        try:
            res = client.models.generate_content(
                model=model_name,
                contents=[image_part, "What color is this square? Reply in 1-2 words."],
            )
            answer = (res.text or "").strip().replace("\n", " ")
            print(f"SUCCESS! -> \"{answer}\"")
            if not working_model:
                working_model = model_name
                break
        except Exception as e:
            err = str(e)
            if "404" in err or "not found" in err.lower():
                print("Unavailable (404 Not Found / Deprecated)")
            elif "429" in err or "quota" in err.lower():
                print("Quota / Rate Limited (429)")
            elif "403" in err or "permission" in err.lower():
                print("Permission Denied (403)")
            else:
                summary = err.split("\n")[0][:60]
                print(f"Failed: {summary}")

    print("\n" + "=" * 60)
    if working_model:
        print(f"[RECOMMENDATION] Set GEMINI_MODEL={working_model} in your .env file.")
        print(f"You can update .env directly or select '{working_model}' in the app sidebar.")
    else:
        print("[WARNING] None of the standard flash candidates succeeded.")
        print("Please verify your API key permissions in Google AI Studio.")
    print("=" * 60)


if __name__ == "__main__":
    run_verification()

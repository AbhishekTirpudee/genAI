"""
Product Image Understanding API
Flask backend that uses Google Gemini Vision to analyze product images
and generate structured product descriptions.

Uses the official google-genai SDK (v2+).
"""

import os
import base64
import json
import re
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from google import genai
from google.genai import types
from PIL import Image
import io

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configure Gemini API
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found. Please set it in your .env file.")

client = genai.Client(api_key=GEMINI_API_KEY)
MODEL = "gemini-3.8-flash"

ANALYSIS_PROMPT = """
You are an expert product analyst with deep knowledge of e-commerce, retail, and product photography.
Analyze the provided product image with extreme detail and return a structured JSON response.

Carefully examine every visible element of the product in the image and provide:

{
  "product_name": "Concise, marketable product name",
  "category": "Primary product category (e.g., Electronics, Clothing, Furniture, etc.)",
  "subcategory": "More specific subcategory",
  "brand": "Brand name if visible, otherwise 'Unknown'",
  "tagline": "A compelling one-line marketing tagline for this product",
  "short_description": "2-3 sentence engaging product summary for e-commerce listing",
  "long_description": "Detailed 4-6 sentence product description covering all features, benefits, and use cases",
  "visual_features": {
    "primary_color": "Main color(s) of the product",
    "secondary_colors": ["List", "of", "additional", "colors"],
    "material": "Visible material(s) the product appears to be made of",
    "finish": "Surface finish (matte, glossy, textured, etc.)",
    "shape": "General shape or form factor",
    "size_estimate": "Estimated relative size (compact, medium, large) with context",
    "design_style": "Design aesthetic (modern, vintage, minimalist, industrial, etc.)"
  },
  "key_features": [
    "Feature 1 with brief explanation",
    "Feature 2 with brief explanation",
    "Feature 3 with brief explanation",
    "Feature 4 with brief explanation",
    "Feature 5 with brief explanation"
  ],
  "specifications": {
    "visible_dimensions": "Any visible size indicators",
    "visible_components": ["Component 1", "Component 2"],
    "visible_labels_text": "Any text, labels, or markings visible on product",
    "connectivity": "Ports, buttons, or connection points if applicable",
    "packaging": "Packaging details if visible"
  },
  "use_cases": [
    "Primary use case",
    "Secondary use case",
    "Tertiary use case"
  ],
  "target_audience": "Who this product is designed for",
  "unique_selling_points": [
    "USP 1",
    "USP 2",
    "USP 3"
  ],
  "condition_assessment": "New/Used/Refurbished based on visible wear",
  "quality_indicators": "Observable quality signals from the image",
  "seo_keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
  "suggested_price_range": "Estimated retail price range based on product type and quality",
  "confidence_score": 0.95
}

IMPORTANT:
- Return ONLY valid JSON, no markdown formatting or code blocks
- Be specific and detailed based on what you actually see in the image
- If something is not visible or unclear, make reasonable inferences based on similar products
- The confidence_score should reflect how certain you are about the overall analysis (0.0 to 1.0)
"""


def validate_image(image_bytes: bytes) -> tuple:
    """Validate that the uploaded file is a valid image."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
        return True, img.format
    except Exception as e:
        return False, str(e)


def analyze_product_image(image_bytes: bytes, mime_type: str) -> dict:
    """
    Send image to Gemini Vision API and get structured product analysis.

    Args:
        image_bytes: Raw image bytes
        mime_type: MIME type of the image

    Returns:
        Parsed JSON dict with product analysis
    """
    # Build the image Part using the new SDK
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)

    response = client.models.generate_content(
        model=MODEL,
        contents=[ANALYSIS_PROMPT, image_part],
        config=types.GenerateContentConfig(
            temperature=0.3,
            max_output_tokens=2048,
        ),
    )

    raw_text = response.text.strip()

    # Strip markdown code fences if present
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)
    raw_text = raw_text.strip()

    result = json.loads(raw_text)
    return result


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy", "model": MODEL})


@app.route("/analyze", methods=["POST"])
def analyze_product():
    """
    Main endpoint: accepts a product image and returns structured analysis.

    Accepts:
        - Multipart form data with 'image' file field
        - JSON body with 'image_base64' and 'mime_type' fields

    Returns:
        JSON with full product analysis
    """
    try:
        image_bytes = None
        mime_type = None

        # Handle multipart form upload
        if "image" in request.files:
            file = request.files["image"]
            if file.filename == "":
                return jsonify({"error": "No file selected"}), 400

            image_bytes = file.read()
            mime_type = file.content_type or "image/jpeg"

        # Handle base64 JSON payload
        elif request.is_json:
            data = request.get_json()
            if "image_base64" not in data:
                return jsonify({"error": "Missing 'image_base64' field"}), 400

            image_bytes = base64.b64decode(data["image_base64"])
            mime_type = data.get("mime_type", "image/jpeg")

        else:
            return jsonify({"error": "No image provided. Use multipart form or JSON with base64."}), 400

        # Validate image
        is_valid, fmt_or_err = validate_image(image_bytes)
        if not is_valid:
            return jsonify({"error": f"Invalid image file: {fmt_or_err}"}), 400

        # Enforce max size (10 MB)
        if len(image_bytes) > 10 * 1024 * 1024:
            return jsonify({"error": "Image too large. Maximum size is 10MB."}), 400

        # Analyze the product image
        analysis = analyze_product_image(image_bytes, mime_type)

        return jsonify({
            "success": True,
            "analysis": analysis,
            "image_size_kb": round(len(image_bytes) / 1024, 2),
        })

    except json.JSONDecodeError as e:
        return jsonify({"error": f"Failed to parse Gemini response as JSON: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Analysis failed: {str(e)}"}), 500


if __name__ == "__main__":
    print("🚀 Product Vision API starting on http://localhost:5000")
    app.run(debug=True, host="0.0.0.0", port=5000)

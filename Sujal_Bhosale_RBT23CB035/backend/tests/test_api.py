import base64
import io
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.services.style_presets import enhance_prompt_with_style

client = TestClient(app)

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DreamCanvas AI"
    assert data["provider"] == "Cloudflare Workers AI"
    assert data["model"] == "@cf/black-forest-labs/flux-1-schnell"

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "model" in data
    assert data["model"] == "@cf/black-forest-labs/flux-1-schnell"

def test_styles_endpoint():
    response = client.get("/api/styles")
    assert response.status_code == 200
    data = response.json()
    assert "styles" in data
    assert len(data["styles"]) > 0
    ids = [s["id"] for s in data["styles"]]
    assert "photorealistic" in ids
    assert "cyberpunk" in ids

def test_style_prompt_enhancement():
    prompt = "A neon sports car"
    enhanced = enhance_prompt_with_style(prompt, "cyberpunk")
    assert "cyberpunk" in enhanced.lower()
    assert "A neon sports car" in enhanced

def test_generate_input_validation():
    # Empty prompt returns 422
    response = client.post("/api/generate", json={"prompt": "   "})
    assert response.status_code == 422

    # Missing prompt
    response = client.post("/api/generate", json={})
    assert response.status_code == 422

def test_generate_missing_account_id_returns_401():
    # When Account ID is not configured, generator raises 401
    with patch("backend.services.cf_generator.settings.CLOUDFLARE_ACCOUNT_ID", ""):
        response = client.post(
            "/api/generate",
            json={"prompt": "A tranquil lake", "style": "photorealistic"}
        )
        assert response.status_code == 401
        assert "Cloudflare Account ID is not configured" in response.json()["error"]

def test_generate_cloudflare_success_json():
    # Create test image in memory
    sample_img = Image.new("RGB", (256, 256), color="cyan")
    buf = io.BytesIO()
    sample_img.save(buf, format="PNG")
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "result": {
            "image": b64_img
        },
        "errors": [],
        "messages": []
    }

    with patch("backend.services.cf_generator.settings.CLOUDFLARE_API_TOKEN", "cfut_test_token"), \
         patch("backend.services.cf_generator.settings.CLOUDFLARE_ACCOUNT_ID", "test_account_123"), \
         patch("httpx.Client.post", return_value=mock_response):

        response = client.post(
            "/api/generate",
            json={
                "prompt": "An astronaut on Mars",
                "style": "photorealistic",
                "num_inference_steps": 4
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["mime_type"] == "image/png"
        assert len(data["image_base64"]) > 0
        assert data["prompt"] == "An astronaut on Mars"
        assert data["width"] == 256
        assert data["height"] == 256

def test_generate_cloudflare_returns_png_bytes():
    # Test returning direct image/png bytes when requested
    sample_img = Image.new("RGB", (128, 128), color="gold")
    buf = io.BytesIO()
    sample_img.save(buf, format="PNG")
    b64_img = base64.b64encode(buf.getvalue()).decode("utf-8")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.json.return_value = {
        "success": True,
        "result": {"image": b64_img}
    }

    with patch("backend.services.cf_generator.settings.CLOUDFLARE_API_TOKEN", "cfut_test_token"), \
         patch("backend.services.cf_generator.settings.CLOUDFLARE_ACCOUNT_ID", "test_account_123"), \
         patch("httpx.Client.post", return_value=mock_response):

        # Test with Accept: image/png header
        response = client.post(
            "/api/generate",
            headers={"Accept": "image/png"},
            json={"prompt": "A golden statue", "style": "none"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"
        # Verify it's a valid PNG header
        assert response.content[:8] == b"\x89PNG\r\n\x1a\n"

        # Test dedicated raw endpoint
        response_raw = client.post(
            "/api/generate/raw",
            json={"prompt": "A golden statue", "style": "none"}
        )
        assert response_raw.status_code == 200
        assert response_raw.headers["content-type"] == "image/png"
        assert response_raw.content[:8] == b"\x89PNG\r\n\x1a\n"

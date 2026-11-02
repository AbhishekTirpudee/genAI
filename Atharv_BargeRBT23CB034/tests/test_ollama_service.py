"""
Unit tests for services/ollama_service.py.
Tests base64 conversion, payload formatting, connection status,
and mocked Ollama vision inference.
"""

from unittest.mock import patch, MagicMock
import io
import json
import urllib.error
import pytest
from PIL import Image

from services.ollama_service import (
    answer_image_question_ollama,
    pil_image_to_base64,
    check_ollama_connection,
    get_ollama_host,
    get_ollama_model,
    OllamaServiceError,
)


def test_pil_image_to_base64():
    """Test: PIL Image converts to valid base64 JPEG string."""
    img = Image.new("RGB", (64, 64), color="blue")
    b64_str = pil_image_to_base64(img)
    assert isinstance(b64_str, str)
    assert len(b64_str) > 50


def test_empty_question_in_ollama():
    """Test: Empty question raises OllamaServiceError."""
    img = Image.new("RGB", (50, 50), color="white")
    with pytest.raises(OllamaServiceError) as exc:
        answer_image_question_ollama(img, "")
    assert "provide a question" in str(exc.value).lower()


@patch("urllib.request.urlopen")
def test_check_ollama_connection_success(mock_urlopen):
    """Test: check_ollama_connection returns True and model list on 200 OK."""
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = json.dumps({
        "models": [{"name": "llama3.2-vision:latest"}, {"name": "llava:latest"}]
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    is_online, models = check_ollama_connection("http://localhost:11434")
    assert is_online is True
    assert "llama3.2-vision:latest" in models
    assert "llava:latest" in models


@patch("urllib.request.urlopen")
def test_check_ollama_connection_failure(mock_urlopen):
    """Test: check_ollama_connection returns False when Ollama is offline."""
    mock_urlopen.side_effect = Exception("Connection refused")
    is_online, models = check_ollama_connection("http://localhost:11434")
    assert is_online is False
    assert models == []


@patch("urllib.request.urlopen")
def test_mock_ollama_single_turn_qa(mock_urlopen):
    """Test: Mock single-turn Ollama vision response."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "message": {"role": "assistant", "content": "The image shows a wooden chess board."}
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    img = Image.new("RGB", (100, 100), color="black")
    answer = answer_image_question_ollama(
        image=img,
        question="What is this?",
        model="llama3.2-vision",
    )
    assert answer == "The image shows a wooden chess board."


@patch("urllib.request.urlopen")
def test_mock_ollama_multi_turn_qa(mock_urlopen):
    """Test: Mock multi-turn Ollama vision response with history."""
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps({
        "message": {"role": "assistant", "content": "The white pieces are in front."}
    }).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_urlopen.return_value = mock_resp

    img = Image.new("RGB", (100, 100), color="black")
    history = [
        {"role": "user", "content": "What is in the image?"},
        {"role": "assistant", "content": "A chess board with pieces."}
    ]
    answer = answer_image_question_ollama(
        image=img,
        question="Where are the white pieces?",
        conversation_history=history,
        model="llama3.2-vision",
    )
    assert answer == "The white pieces are in front."


@patch("urllib.request.urlopen")
def test_ollama_model_not_found_handling(mock_urlopen):
    """Test: 404 Model not found raises informative message with 'ollama run'."""
    fp = io.BytesIO(json.dumps({"error": "model 'llama3.2-vision' not found"}).encode("utf-8"))
    mock_urlopen.side_effect = urllib.error.HTTPError(
        url="http://localhost:11434/api/chat",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=fp
    )

    img = Image.new("RGB", (50, 50), color="red")
    with pytest.raises(OllamaServiceError) as exc:
        answer_image_question_ollama(img, "What is this?", model="llama3.2-vision")
    assert "ollama run llama3.2-vision" in str(exc.value)

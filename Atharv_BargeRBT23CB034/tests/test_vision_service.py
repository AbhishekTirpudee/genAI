"""
Unit tests for services/vision_service.py.
Tests missing API key handling, AI error masking, and mock response generation
without requiring external network calls.
"""

from unittest.mock import patch, MagicMock
import pytest
from PIL import Image

from services.vision_service import (
    answer_image_question,
    get_api_key,
    get_configured_model,
    VisionServiceError,
    SYSTEM_INSTRUCTION,
)


def test_missing_api_key_handling(monkeypatch):
    """Test 9: Missing API key handling raises clean VisionServiceError."""
    # Ensure environment variables are clear
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    with pytest.raises(VisionServiceError) as exc_info:
        get_api_key(override_key="")
    assert "Gemini API key is not configured" in str(exc_info.value)

    # Placeholder API key should also be rejected
    with pytest.raises(VisionServiceError) as exc_info:
        get_api_key(override_key="your_api_key")
    assert "Gemini API key is not configured" in str(exc_info.value)


def test_empty_question_in_vision_service():
    """Test: Empty question passed to answer_image_question raises VisionServiceError."""
    img = Image.new("RGB", (100, 100), color="blue")
    with pytest.raises(VisionServiceError) as exc:
        answer_image_question(image=img, question="", api_key="fake-key-12345")
    assert "provide a question" in str(exc.value).lower()


def test_invalid_image_type_in_vision_service():
    """Test: Passing invalid non-image type raises VisionServiceError."""
    with pytest.raises(VisionServiceError) as exc:
        answer_image_question(image=12345, question="What is this?", api_key="fake-key-12345")
    assert "Failed to process image" in str(exc.value) or "Unsupported" in str(exc.value)


@patch("services.vision_service._call_with_google_genai_sdk")
def test_mock_single_turn_vision_qa(mock_call):
    """Test: Mock single-turn vision QA generates expected response."""
    mock_call.return_value = "The image shows a blue ceramic coffee mug on a wooden table."
    
    img = Image.new("RGB", (200, 200), color="blue")
    answer = answer_image_question(
        image=img,
        question="What object is visible?",
        api_key="valid-mock-key-12345",
        model_name="gemini-2.5-flash",
    )
    
    assert answer == "The image shows a blue ceramic coffee mug on a wooden table."
    assert mock_call.called
    args, kwargs = mock_call.call_args
    assert kwargs["question"] == "What object is visible?"
    assert kwargs["model_name"] == "gemini-2.5-flash"
    assert kwargs["conversation_history"] == []


@patch("services.vision_service._call_with_google_genai_sdk")
def test_mock_multi_turn_follow_up_qa(mock_call):
    """Test: Multi-turn conversation history is passed to model."""
    mock_call.return_value = "It might be used for hot tea or coffee."
    
    img = Image.new("RGB", (200, 200), color="blue")
    history = [
        {"role": "user", "content": "What is in the image?"},
        {"role": "assistant", "content": "A blue ceramic coffee mug."}
    ]
    
    answer = answer_image_question(
        image=img,
        question="What is it typically used for?",
        conversation_history=history,
        api_key="valid-mock-key-12345",
    )
    
    assert answer == "It might be used for hot tea or coffee."
    assert mock_call.called
    args, kwargs = mock_call.call_args
    assert len(kwargs["conversation_history"]) == 2
    assert kwargs["question"] == "What is it typically used for?"


@patch("services.vision_service._call_with_google_genai_sdk")
def test_quota_exceeded_error_mapping(mock_call):
    """Test: 429 ResourceExhausted is mapped to user-friendly message."""
    mock_call.side_effect = Exception("429 ResourceExhausted: Quota exceeded for quota group")
    
    img = Image.new("RGB", (100, 100), color="white")
    with pytest.raises(VisionServiceError) as exc:
        answer_image_question(image=img, question="What is this?", api_key="fake-key-12345")
    assert "quota exceeded" in str(exc.value).lower()

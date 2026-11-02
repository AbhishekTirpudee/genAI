"""
Helper utilities for VisionQA.
Provides conversation ID generation, session state initialization,
and question/text input validation.
"""

import uuid
import re
from typing import Dict, Any, List, Optional


def generate_conversation_id() -> str:
    """Generate a unique conversation identifier."""
    return str(uuid.uuid4())


def validate_question(question: Optional[str], max_length: int = 1000) -> str:
    """
    Validate that the question is non-empty, not solely whitespace,
    and does not exceed maximum allowable length.
    
    Args:
        question: The user's input question string.
        max_length: Maximum allowed character length.
        
    Returns:
        Cleaned, stripped question string.
        
    Raises:
        ValueError: If question is empty or invalid.
    """
    if question is None:
        raise ValueError("Question cannot be empty. Please ask a question about your image.")
    
    cleaned = question.strip()
    if not cleaned:
        raise ValueError("Question cannot be empty or only spaces.")
        
    if len(cleaned) > max_length:
        raise ValueError(
            f"Question exceeds maximum allowed length of {max_length} characters "
            f"(received {len(cleaned)} characters)."
        )
        
    return cleaned


def mask_api_key(api_key: Optional[str]) -> str:
    """
    Safely mask an API key for safe UI status display without revealing sensitive secrets.
    Example: 'AIzaSyDe...' -> 'AIza...f9a2'
    """
    if not api_key:
        return "Not Set"
    key_str = str(api_key).strip()
    if len(key_str) <= 8:
        return "••••••••"
    return f"{key_str[:4]}••••{key_str[-4:]}"


def init_session_state(session_state: Dict[str, Any]) -> None:
    """
    Initialize all required Streamlit session state keys if not already set.
    
    Args:
        session_state: Streamlit st.session_state object or dictionary.
    """
    if "conversation_id" not in session_state or not session_state["conversation_id"]:
        session_state["conversation_id"] = generate_conversation_id()

    if "messages" not in session_state:
        session_state["messages"] = []

    if "uploaded_image" not in session_state:
        session_state["uploaded_image"] = None

    if "image_metadata" not in session_state:
        session_state["image_metadata"] = None

    if "uploader_key" not in session_state:
        session_state["uploader_key"] = 0

    if "image_id" not in session_state:
        session_state["image_id"] = None

    if "clarity_info" not in session_state:
        session_state["clarity_info"] = None


def reset_conversation(session_state: Dict[str, Any], clear_image: bool = True) -> None:
    """
    Reset conversation state for a New Chat or Image change.
    
    Args:
        session_state: Streamlit st.session_state object.
        clear_image: Whether to also clear the uploaded image.
    """
    session_state["conversation_id"] = generate_conversation_id()
    session_state["messages"] = []
    
    if clear_image:
        session_state["uploaded_image"] = None
        session_state["image_metadata"] = None
        session_state["image_id"] = None
        session_state["clarity_info"] = None
        # Increment uploader_key to reset the st.file_uploader widget
        session_state["uploader_key"] = session_state.get("uploader_key", 0) + 1

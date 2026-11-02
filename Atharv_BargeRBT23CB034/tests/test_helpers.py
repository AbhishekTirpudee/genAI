"""
Unit tests for utils/helpers.py and utils/db.py.
Tests empty question rejection, session initialization, New Chat reset,
and conversation history preservation.
"""

import os
import tempfile
import pytest

from utils.helpers import (
    generate_conversation_id,
    validate_question,
    mask_api_key,
    init_session_state,
    reset_conversation,
)
from utils.db import (
    init_db,
    save_conversation_meta,
    save_message_to_db,
    load_conversation_messages,
    get_saved_conversations,
)


def test_empty_question_rejection():
    """Test 6: Empty or whitespace-only question rejection."""
    with pytest.raises(ValueError) as exc:
        validate_question("")
    assert "empty" in str(exc.value).lower()

    with pytest.raises(ValueError) as exc:
        validate_question("   \t\n  ")
    assert "empty" in str(exc.value).lower()

    with pytest.raises(ValueError) as exc:
        validate_question(None)
    assert "empty" in str(exc.value).lower()


def test_valid_question_cleaning():
    """Test: Question whitespace stripping and valid text acceptance."""
    q = "   What color is the car?   "
    cleaned = validate_question(q)
    assert cleaned == "What color is the car?"


def test_oversized_question_rejection():
    """Test: Rejecting questions exceeding length limit."""
    long_q = "a" * 1500
    with pytest.raises(ValueError) as exc:
        validate_question(long_q, max_length=500)
    assert "exceeds maximum allowed length" in str(exc.value)


def test_mask_api_key():
    """Test: API key masking preserves privacy."""
    assert mask_api_key("") == "Not Set"
    assert mask_api_key(None) == "Not Set"
    masked = mask_api_key("AIzaSyB123456789XyZ0")
    assert masked.startswith("AIza")
    assert masked.endswith("XyZ0")
    assert "123456789" not in masked


def test_conversation_id_generation():
    """Test: Conversation ID generation is unique."""
    id1 = generate_conversation_id()
    id2 = generate_conversation_id()
    assert id1 != id2
    assert len(id1) >= 32


def test_session_state_initialization():
    """Test: Session state dictionary is populated with default keys."""
    state = {}
    init_session_state(state)
    assert "conversation_id" in state
    assert state["messages"] == []
    assert state["uploaded_image"] is None
    assert state["uploader_key"] == 0


def test_new_chat_reset_functionality():
    """Test 8: New Chat functionality resets messages, image, and creates new ID."""
    state = {
        "conversation_id": "old-uuid-1234",
        "messages": [{"role": "user", "content": "hello"}],
        "uploaded_image": "fake_image_obj",
        "image_metadata": {"size": 100},
        "uploader_key": 5,
    }
    
    reset_conversation(state, clear_image=True)
    
    assert state["conversation_id"] != "old-uuid-1234"
    assert state["messages"] == []
    assert state["uploaded_image"] is None
    assert state["image_metadata"] is None
    assert state["uploader_key"] == 6


def test_conversation_history_preservation_sqlite():
    """Test 7: Conversation history preservation and retrieval via SQLite."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name

    try:
        init_db(db_path)
        conv_id = "test-conv-001"
        save_conversation_meta(conv_id, title="Test Image QA", metadata_str="JPEG 800x600", db_path=db_path)
        
        # Save multi-turn conversation
        save_message_to_db(conv_id, "user", "What is in the picture?", db_path=db_path)
        save_message_to_db(conv_id, "assistant", "A cat sitting on a rug.", db_path=db_path)
        save_message_to_db(conv_id, "user", "What color is the cat?", db_path=db_path)
        save_message_to_db(conv_id, "assistant", "The cat is orange tabby.", db_path=db_path)

        messages = load_conversation_messages(conv_id, db_path=db_path)
        assert len(messages) == 4
        assert messages[0] == {"role": "user", "content": "What is in the picture?"}
        assert messages[1] == {"role": "assistant", "content": "A cat sitting on a rug."}
        assert messages[2] == {"role": "user", "content": "What color is the cat?"}
        assert messages[3] == {"role": "assistant", "content": "The cat is orange tabby."}

        # Check list of conversations
        saved_list = get_saved_conversations(db_path=db_path)
        assert len(saved_list) == 1
        assert saved_list[0]["conversation_id"] == conv_id
        assert saved_list[0]["message_count"] == 4
    finally:
        if os.path.exists(db_path):
            os.remove(db_path)

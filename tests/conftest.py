"""Pytest configuration and fixtures for testing."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock

from openvino_genai_chat.storage.json_backend import JSONStorage
from openvino_genai_chat.models.chat_manager import ChatManager
from openvino_genai_chat.templates.template_manager import TemplateManager


@pytest.fixture
def temp_storage_dir():
    """Create a temporary directory for storage tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def json_storage(temp_storage_dir):
    """Create a JSON storage instance with temporary directory."""
    return JSONStorage(temp_storage_dir)


@pytest.fixture
def chat_manager(json_storage):
    """Create a chat manager instance."""
    return ChatManager(json_storage)


@pytest.fixture
def template_manager():
    """Create a template manager instance."""
    return TemplateManager()


@pytest.fixture
def sample_conversation_data():
    """Sample conversation data for testing."""
    return {
        "metadata": {
            "id": "test-conv-1",
            "title": "Test Conversation",
            "created_date": "2026-04-16T10:00:00",
            "updated_date": "2026-04-16T10:30:00",
            "model_name": "test-model",
            "model_device": "CPU",
            "max_tokens": 4096,
            "use_thinking": False,
            "message_count": 2,
        },
        "messages": [
            {
                "role": "user",
                "content": "Hello!",
                "timestamp": "2026-04-16T10:00:00",
            },
            {
                "role": "assistant",
                "content": "Hi! How can I help you?",
                "timestamp": "2026-04-16T10:00:05",
            },
        ],
    }

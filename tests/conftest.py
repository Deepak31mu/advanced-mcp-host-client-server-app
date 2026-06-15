"""Pytest configuration and fixtures for MCP tests."""

import pytest
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import asyncio


@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_workspace():
    """Create a temporary workspace directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        yield workspace


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary config file."""
    config_data = {
        "openai": {
            "api_key": "${OPENAI_API_KEY}",
            "model": "gpt-4o-mini"
        },
        "server": {
            "host": "127.0.0.1",
            "port": 8000
        },
        "gui": {
            "host": "127.0.0.1",
            "port": 7862
        },
        "logging": {
            "level": "INFO"
        }
    }
    config_file = tmp_path / "mcp_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    yield config_file


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_message = MagicMock()
    mock_message.content = "Test response"
    mock_message.tool_calls = None
    mock_response.choices = [MagicMock(message=mock_message)]
    mock_client.chat.completions.create.return_value = mock_response
    return mock_client


@pytest.fixture
def sample_test_file(temp_workspace):
    """Create a sample test file in workspace."""
    test_file = temp_workspace / "test.txt"
    test_file.write_text("This is a test file content.")
    return test_file


@pytest.fixture
def sample_json_file(temp_workspace):
    """Create a sample JSON file in workspace."""
    json_file = temp_workspace / "data.json"
    data = {"key": "value", "number": 42}
    json_file.write_text(json.dumps(data))
    return json_file


@pytest.fixture(autouse=True)
def mock_logging():
    """Mock logging to reduce noise in tests."""
    with patch('logging.getLogger') as mock_logger:
        yield mock_logger

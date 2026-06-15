"""Tests for mcp_config.py module."""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_config import ConfigManager


class TestConfigManagerInit:
    """Test ConfigManager initialization."""

    def test_init_with_config_file(self, temp_config_file):
        """Test initialization with explicit config file."""
        config = ConfigManager(config_file=str(temp_config_file))
        assert config.config_file == str(temp_config_file)
        assert config.config is not None

    def test_init_without_config_file(self, tmp_path):
        """Test initialization without config file uses defaults."""
        # Change to temp directory to avoid finding real config
        with patch('mcp_config.Path') as mock_path:
            mock_path.return_value.parent = tmp_path
            config = ConfigManager(config_file=str(tmp_path / "nonexistent.json"))
            assert config.config == {}

    def test_config_file_not_found_graceful(self, tmp_path):
        """Test graceful handling when config file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.json"
        config = ConfigManager(config_file=str(nonexistent))
        assert config.config == {}


class TestConfigLoad:
    """Test configuration loading."""

    def test_load_valid_json(self, temp_config_file):
        """Test loading valid JSON config."""
        config = ConfigManager(config_file=str(temp_config_file))
        assert "openai" in config.config
        assert config.config["openai"]["model"] == "gpt-4o-mini"

    def test_load_invalid_json(self, tmp_path):
        """Test loading invalid JSON config."""
        bad_config = tmp_path / "bad.json"
        bad_config.write_text("{invalid json")
        config = ConfigManager(config_file=str(bad_config))
        assert config.config == {}

    def test_empty_config_file(self, tmp_path):
        """Test loading empty JSON config."""
        empty_config = tmp_path / "empty.json"
        empty_config.write_text("{}")
        config = ConfigManager(config_file=str(empty_config))
        assert config.config == {}


class TestEnvironmentVariableSubstitution:
    """Test environment variable substitution in config."""

    def test_substitute_env_var_in_string(self, temp_config_file):
        """Test substitution of environment variable."""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-test-key-123'}):
            config = ConfigManager(config_file=str(temp_config_file))
            assert config.config["openai"]["api_key"] == "sk-test-key-123"

    def test_substitute_missing_env_var(self, temp_config_file):
        """Test handling of missing environment variable."""
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigManager(config_file=str(temp_config_file))
            # Should keep placeholder if env var not found
            assert config.config["openai"]["api_key"] == "${OPENAI_API_KEY}"

    def test_substitute_nested_env_vars(self, tmp_path):
        """Test substitution in nested config."""
        config_data = {
            "nested": {
                "value": "${TEST_VAR}"
            }
        }
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with patch.dict(os.environ, {'TEST_VAR': 'test_value'}):
            config = ConfigManager(config_file=str(config_file))
            assert config.config["nested"]["value"] == "test_value"


class TestConfigGetMethods:
    """Test configuration get methods."""

    def test_get_openai_model_from_config(self, temp_config_file):
        """Test getting model from config file."""
        config = ConfigManager(config_file=str(temp_config_file))
        model = config.get_openai_model()
        assert model == "gpt-4o-mini"

    def test_get_openai_model_override(self, temp_config_file):
        """Test override parameter for model."""
        config = ConfigManager(config_file=str(temp_config_file))
        model = config.get_openai_model(override="gpt-4o")
        assert model == "gpt-4o"

    def test_get_openai_model_from_env(self, tmp_path):
        """Test getting model from environment variable."""
        config_file = tmp_path / "empty.json"
        config_file.write_text("{}")
        
        with patch.dict(os.environ, {'OPENAI_MODEL': 'gpt-4-turbo'}):
            config = ConfigManager(config_file=str(config_file))
            model = config.get_openai_model()
            assert model == "gpt-4-turbo"

    def test_get_openai_model_default(self, tmp_path):
        """Test default model when not configured."""
        config_file = tmp_path / "empty.json"
        config_file.write_text("{}")
        
        with patch.dict(os.environ, {}, clear=True):
            config = ConfigManager(config_file=str(config_file))
            model = config.get_openai_model()
            assert model == "gpt-4o-mini"

    def test_get_openai_api_key_from_config(self, tmp_path):
        """Test getting API key from config."""
        config_data = {
            "openai": {
                "api_key": "sk-direct-key-123"
            }
        }
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        config = ConfigManager(config_file=str(config_file))
        api_key = config.get_openai_api_key()
        assert api_key == "sk-direct-key-123"

    def test_get_openai_api_key_override(self, temp_config_file):
        """Test API key override."""
        config = ConfigManager(config_file=str(temp_config_file))
        api_key = config.get_openai_api_key(override="sk-override-key")
        assert api_key == "sk-override-key"

    def test_get_server_host(self, temp_config_file):
        """Test getting server host."""
        config = ConfigManager(config_file=str(temp_config_file))
        host = config.get_server_host()
        assert host == "127.0.0.1"

    def test_get_server_port(self, temp_config_file):
        """Test getting server port."""
        config = ConfigManager(config_file=str(temp_config_file))
        port = config.get_server_port()
        assert port == 8000

    def test_get_gui_host(self, temp_config_file):
        """Test getting GUI host."""
        config = ConfigManager(config_file=str(temp_config_file))
        host = config.get_gui_host()
        assert host == "127.0.0.1"

    def test_get_gui_port(self, temp_config_file):
        """Test getting GUI port."""
        config = ConfigManager(config_file=str(temp_config_file))
        port = config.get_gui_port()
        assert port == 7862

    def test_get_log_level(self, temp_config_file):
        """Test getting log level."""
        config = ConfigManager(config_file=str(temp_config_file))
        level = config.get_log_level()
        assert level == "INFO"

    def test_get_nested_value(self, temp_config_file):
        """Test getting nested value with dot notation."""
        config = ConfigManager(config_file=str(temp_config_file))
        model = config.get("openai.model")
        assert model == "gpt-4o-mini"

    def test_get_with_default(self, tmp_path):
        """Test get with default value."""
        config_file = tmp_path / "empty.json"
        config_file.write_text("{}")
        config = ConfigManager(config_file=str(config_file))
        value = config.get("nonexistent.key", default="default_value")
        assert value == "default_value"


class TestConfigPriority:
    """Test configuration priority resolution."""

    def test_override_takes_priority(self, temp_config_file):
        """Test that override parameter takes highest priority."""
        with patch.dict(os.environ, {'OPENAI_MODEL': 'gpt-4-env'}):
            config = ConfigManager(config_file=str(temp_config_file))
            model = config.get_openai_model(override='gpt-4o-override')
            assert model == "gpt-4o-override"

    def test_config_overrides_env(self, tmp_path):
        """Test that config file overrides environment."""
        config_data = {"openai": {"model": "gpt-4-config"}}
        config_file = tmp_path / "config.json"
        with open(config_file, 'w') as f:
            json.dump(config_data, f)
        
        with patch.dict(os.environ, {'OPENAI_MODEL': 'gpt-4-env'}):
            config = ConfigManager(config_file=str(config_file))
            model = config.get_openai_model()
            assert model == "gpt-4-config"

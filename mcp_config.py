"""Configuration management module for MCP HTTP Host App."""

import json
import os
import logging
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages application configuration from JSON file and environment."""

    def __init__(self, config_file: str = None):
        """
        Initialize config manager.

        Args:
            config_file: Path to config JSON file. If None, looks for mcp_config.json
                        in the script directory.
        """
        self.config_file = config_file or self._find_config_file()
        self.config = {}
        self._load_config()

    def _find_config_file(self) -> str:
        """Find config file in standard locations."""
        # Look for mcp_config.json in script directory
        script_dir = Path(__file__).parent
        config_path = script_dir / "mcp_config.json"

        if config_path.exists():
            logger.debug(f"Found config file: {config_path}")
            return str(config_path)

        # If not found, create a default one
        logger.warning(f"Config file not found at {config_path}. Will use environment variables and defaults.")
        return str(config_path)

    def _load_config(self):
        """Load configuration from JSON file."""
        if not os.path.exists(self.config_file):
            logger.warning(f"Config file not found: {self.config_file}. Using environment variables and defaults.")
            self.config = {}
            return

        try:
            with open(self.config_file, 'r') as f:
                self.config = json.load(f)
            logger.info(f"Loaded configuration from {self.config_file}")

            # Substitute environment variables in config
            self._substitute_env_vars()

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {self.config_file}: {e}")
            self.config = {}
        except Exception as e:
            logger.error(f"Error loading config file {self.config_file}: {e}")
            self.config = {}

    def _substitute_env_vars(self):
        """Recursively substitute ${VAR} patterns with environment variables."""
        def substitute(obj):
            if isinstance(obj, str):
                # Replace ${VAR} patterns with environment variables
                if obj.startswith("${") and obj.endswith("}"):
                    var_name = obj[2:-1]
                    env_value = os.getenv(var_name)
                    if env_value:
                        logger.debug(f"Substituted ${{{var_name}}} from environment")
                        return env_value
                    else:
                        logger.debug(f"Environment variable {var_name} not found, keeping placeholder")
                        return obj
                return obj
            elif isinstance(obj, dict):
                return {k: substitute(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [substitute(item) for item in obj]
            return obj

        self.config = substitute(self.config)

    def get(self, key: str, default: Any = None, section: Optional[str] = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key (can be nested with dots, e.g., "openai.model")
            default: Default value if key not found
            section: Optional section to search in

        Returns:
            Configuration value or default
        """
        # Handle nested keys like "openai.model"
        if "." in key:
            keys = key.split(".")
            value = self.config
            for k in keys:
                if isinstance(value, dict):
                    value = value.get(k)
                    if value is None:
                        return default
                else:
                    return default
            return value

        # Check in specific section if provided
        if section and section in self.config:
            return self.config[section].get(key, default)

        # Check at root level
        return self.config.get(key, default)

    def get_openai_model(self, override: str = None) -> str:
        """Get OpenAI model with fallback chain."""
        # Priority: override > config file > env var > default
        if override:
            logger.debug(f"Using OpenAI model from override: {override}")
            return override

        model = self.get("openai.model")
        if model:
            logger.debug(f"Using OpenAI model from config: {model}")
            return model

        model = os.getenv("OPENAI_MODEL")
        if model:
            logger.debug(f"Using OpenAI model from OPENAI_MODEL env var: {model}")
            return model

        default_model = "gpt-4o-mini"
        logger.debug(f"Using default OpenAI model: {default_model}")
        return default_model

    def get_openai_api_key(self, override: str = None) -> Optional[str]:
        """Get OpenAI API key with fallback chain."""
        # Priority: override > config file > env var
        if override:
            logger.debug("Using OpenAI API key from override")
            return override

        api_key = self.get("openai.api_key")
        if api_key and api_key != "${OPENAI_API_KEY}":
            logger.debug("Using OpenAI API key from config file")
            return api_key

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            logger.debug("Using OpenAI API key from OPENAI_API_KEY env var")
            return api_key

        logger.debug("No OpenAI API key found in config or environment")
        return None

    def get_server_host(self, override: str = None) -> str:
        """Get server host."""
        return override or self.get("server.host", "127.0.0.1")

    def get_server_port(self, override: int = None) -> int:
        """Get server port."""
        if override:
            return override
        port = self.get("server.port", 8000)
        return int(port) if isinstance(port, str) else port

    def get_gui_host(self, override: str = None) -> str:
        """Get GUI host."""
        return override or os.getenv("MCP_HOST_HOST", self.get("gui.host", "127.0.0.1"))

    def get_gui_port(self, override: int = None) -> int:
        """Get GUI port."""
        if override:
            return override
        port = os.getenv("MCP_HOST_PORT", self.get("gui.port", 7862))
        return int(port) if isinstance(port, str) else port

    def get_log_level(self) -> str:
        """Get logging level."""
        return os.getenv("LOG_LEVEL", self.get("logging.level", "INFO"))

    def print_summary(self):
        """Print configuration summary."""
        logger.info("=" * 60)
        logger.info("Configuration Summary")
        logger.info("=" * 60)
        logger.info(f"Config File: {self.config_file}")
        logger.info(f"OpenAI Model: {self.get_openai_model()}")
        logger.info(f"OpenAI API Key: {'Configured' if self.get_openai_api_key() else 'Not configured'}")
        logger.info(f"Server: {self.get_server_host()}:{self.get_server_port()}")
        logger.info(f"GUI: {self.get_gui_host()}:{self.get_gui_port()}")
        logger.info(f"Log Level: {self.get_log_level()}")
        logger.info("=" * 60)

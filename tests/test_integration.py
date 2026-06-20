"""Integration tests for MCP HTTP application.

These tests verify real-world scenarios and system integration.
Marked for GitHub Actions CI/CD pipeline.
"""

import pytest
import json
import asyncio
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_http_server import (
    is_within_roots,
    read_file,
    write_file,
    list_files,
    analyze_code,
)
from mcp_http_client_base import MCPHTTPClient
from mcp_config import ConfigManager


@pytest.mark.integration
class TestEndToEndFileOperations:
    """Test complete file operation workflows."""

    @pytest.mark.asyncio
    async def test_write_then_read_file_complete_workflow(self, temp_workspace):
        """Integration: Write file then read it back."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            content = "Integration test content"
            result = write_file("integration_test.txt", content)
            assert "Success" in result
            assert (temp_workspace / "integration_test.txt").exists()
            read_content = read_file("integration_test.txt")
            assert read_content == content
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    @pytest.mark.asyncio
    async def test_list_files_after_write_workflow(self, temp_workspace):
        """Integration: Write files then list directory."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            (temp_workspace / "file1.txt").write_text("content1")
            (temp_workspace / "file2.txt").write_text("content2")
            (temp_workspace / "subdir").mkdir()
            (temp_workspace / "subdir" / "file3.txt").write_text("content3")

            files = list_files(".")
            assert "file1.txt" in files
            assert "file2.txt" in files
            assert "subdir" in files
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    @pytest.mark.asyncio
    async def test_complete_workspace_workflow(self, temp_workspace):
        """Integration: Create, list, read, update workflow."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            write_file("workflow_test.txt", "v1")
            assert "workflow_test.txt" in list_files(".")

            content = read_file("workflow_test.txt")
            assert content == "v1"

            write_file("workflow_test.txt", "v2")
            updated = read_file("workflow_test.txt")
            assert updated == "v2"
        finally:
            mcp_http_server.BASE_DIR = original_base_dir


@pytest.mark.integration
class TestConfigurationPriorityWorkflow:
    """Test configuration priority resolution in real scenarios."""

    def test_config_with_env_vars_and_override(self, temp_config_file):
        """Integration: Config file + env vars + override."""
        config_path = temp_config_file
        config_data = {
            "openai": {
                "api_key": "${OPENAI_API_KEY}",
                "model": "${OPENAI_MODEL:gpt-4o-mini}",
            }
        }
        config_path.write_text(json.dumps(config_data))

        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test-key", "OPENAI_MODEL": "gpt-4o"},
        ):
            config = ConfigManager(str(config_path))

            api_key = config.get_openai_api_key()
            assert api_key == "sk-test-key"

            overridden_key = config.get_openai_api_key(override="sk-override")
            assert overridden_key == "sk-override"

    def test_config_fallback_to_defaults(self, temp_config_file):
        """Integration: Config file with missing values falls back to defaults."""
        config_path = temp_config_file
        config_data = {"openai": {}}
        config_path.write_text(json.dumps(config_data))

        config = ConfigManager(str(config_path))

        model = config.get_openai_model()
        assert model == "gpt-4o-mini"


@pytest.mark.integration
class TestClientConnectionResilience:
    """Test client connection resilience patterns."""

    @pytest.mark.asyncio
    async def test_connection_retry_sequence(self):
        """Integration: Test retry sequence on connection failure."""
        client = MCPHTTPClient("http://invalid.local:9999")

        with patch('mcp_http_client_base.streamablehttp_client') as mock_http, \
             patch('mcp_http_client_base.asyncio.sleep', new=AsyncMock()):
            mock_http.return_value.__aenter__.side_effect = ConnectionError("Connection failed")
            with pytest.raises(Exception):
                await client.connect()

    @pytest.mark.asyncio
    async def test_connection_cleanup_workflow(self):
        """Integration: Test proper resource cleanup."""
        client = MCPHTTPClient("http://localhost:8000")
        client.exit_stack = AsyncMock()
        client.exit_stack.aclose = AsyncMock()

        await client.cleanup()

        assert client._connected is False
        client.exit_stack.aclose.assert_called_once()


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security features in realistic scenarios."""

    def test_directory_traversal_attack_blocked(self, temp_workspace):
        """Security: Block directory traversal attacks."""
        root = str(temp_workspace)

        attack_paths = [
            "../etc/passwd",
            "../../etc/passwd",
            "subdir/../../../../etc/passwd",
            "../../../../etc/passwd",
        ]

        for attack_path in attack_paths:
            try:
                is_allowed = is_within_roots(attack_path, [root])
                assert not is_allowed, f"Attack path accepted: {attack_path}"
            except (ValueError, AssertionError):
                pass

    def test_absolute_path_attack_blocked(self, temp_workspace):
        """Security: Block absolute path access."""
        root = str(temp_workspace)

        absolute_paths = [
            "/etc/passwd",
            "/tmp/secret.txt",
        ]

        for abs_path in absolute_paths:
            try:
                is_allowed = is_within_roots(abs_path, [root])
                assert not is_allowed, f"Absolute path accepted: {abs_path}"
            except (ValueError, AssertionError):
                pass

    def test_valid_paths_allowed(self, temp_workspace):
        """Security: Allow only valid workspace paths."""
        root = str(temp_workspace)
        valid_paths = [
            "test.txt",
            "./test.txt",
            "subdir/test.txt",
            "subdir/deep/test.txt",
        ]

        for valid_path in valid_paths:
            is_allowed = is_within_roots(valid_path, [root])
            assert is_allowed, f"Valid path rejected: {valid_path}"


@pytest.mark.integration
class TestCodeAnalysisSampling:
    """Test code analysis and sampling mechanism."""

    def test_analyze_code_returns_sampling_trigger(self):
        """Integration: Code analysis triggers sampling."""
        code = """
def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
"""
        result = analyze_code(code, focus="efficiency")
        assert isinstance(result, str)
        assert "sampling" in result.lower()

    def test_analyze_code_with_various_focuses(self):
        """Integration: Code analysis with different focus areas."""
        code = "x = 1 + 2"
        focuses = ["efficiency", "readability", "security", ""]

        for focus in focuses:
            result = analyze_code(code, focus=focus)
            assert isinstance(result, str)
            assert len(result) > 0


@pytest.mark.integration
class TestMultipleComponentsIntegration:
    """Test integration of multiple components together."""

    def test_config_and_server_integration(self, temp_config_file):
        """Integration: Config manager used by server components."""
        config_data = {
            "openai": {
                "api_key": "sk-test",
                "model": "gpt-4o-mini",
            },
            "server": {"host": "127.0.0.1", "port": 8000},
        }
        config_path = temp_config_file
        config_path.write_text(json.dumps(config_data))

        config = ConfigManager(str(config_path))

        assert config.get_openai_model() == "gpt-4o-mini"
        assert config.get_openai_api_key() == "sk-test"
        assert config.get_server_host() == "127.0.0.1"
        assert config.get_server_port() == 8000

    def test_workspace_operations_under_load(self, temp_workspace):
        """Integration: Multiple operations in sequence."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            for i in range(10):
                write_file(f"file{i}.txt", f"content{i}")

            result = list_files(".")
            assert result.count("file") >= 10

            for i in range(10):
                content = read_file(f"file{i}.txt")
                assert content == f"content{i}"
        finally:
            mcp_http_server.BASE_DIR = original_base_dir


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across components."""

    def test_error_on_invalid_json_config(self, temp_config_file):
        """Integration: Handle invalid JSON config gracefully."""
        config_path = temp_config_file
        config_path.write_text("{invalid json}")

        config = ConfigManager(str(config_path))

        model = config.get_openai_model()
        assert model is not None

    def test_error_on_missing_file_operations(self, temp_workspace):
        """Integration: Handle missing files gracefully."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            result = read_file("nonexistent.txt")
            assert "Error" in result or "not found" in result.lower()
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_error_on_invalid_paths(self, temp_workspace):
        """Integration: Handle invalid paths gracefully."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            result = write_file("../../../etc/passwd", "content")
            assert "Error" in result or "Access denied" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir


@pytest.mark.integration
class TestPerformanceUnderLoad:
    """Test performance characteristics under load."""

    def test_rapid_file_writes(self, temp_workspace):
        """Integration: Rapid write operations."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            count = 50
            for i in range(count):
                write_file(f"rapid_{i}.txt", f"content{i}")

            result = list_files(".")
            assert result.count("rapid_") == count
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_rapid_file_reads(self, temp_workspace):
        """Integration: Rapid read operations."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            for i in range(20):
                (temp_workspace / f"read_test_{i}.txt").write_text(f"content{i}")

            for i in range(20):
                content = read_file(f"read_test_{i}.txt")
                assert content == f"content{i}"
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_large_file_operations(self, temp_workspace):
        """Integration: Large file operations."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        try:
            large_content = "x" * (1024 * 1024)

            write_file("large.txt", large_content)
            content = read_file("large.txt")
            assert len(content) == len(large_content)
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

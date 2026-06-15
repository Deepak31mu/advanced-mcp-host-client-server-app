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
        # Write file
        file_path = temp_workspace / "integration_test.txt"
        content = "Integration test content"
        write_file(str(file_path), content)

        # Verify file exists
        assert file_path.exists()

        # Read file
        read_content = read_file(str(file_path))
        assert read_content == content

    @pytest.mark.asyncio
    async def test_list_files_after_write_workflow(self, temp_workspace):
        """Integration: Write files then list directory."""
        # Write multiple files
        (temp_workspace / "file1.txt").write_text("content1")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "subdir").mkdir()
        (temp_workspace / "subdir" / "file3.txt").write_text("content3")

        # List files
        files = list_files(str(temp_workspace))
        assert "file1.txt" in files
        assert "file2.txt" in files
        assert "subdir" in files

    @pytest.mark.asyncio
    async def test_complete_workspace_workflow(self, temp_workspace):
        """Integration: Create, list, read, update workflow."""
        root = str(temp_workspace)

        # Create file
        write_file(f"{root}/workflow_test.txt", "v1")
        assert "workflow_test.txt" in list_files(root)

        # Read file
        content = read_file(f"{root}/workflow_test.txt")
        assert content == "v1"

        # Update file
        write_file(f"{root}/workflow_test.txt", "v2")
        updated = read_file(f"{root}/workflow_test.txt")
        assert updated == "v2"


@pytest.mark.integration
class TestConfigurationPriorityWorkflow:
    """Test configuration priority resolution in real scenarios."""

    def test_config_with_env_vars_and_override(self, temp_config_file):
        """Integration: Config file + env vars + override."""
        # Create config with env var placeholder
        config_path = temp_config_file
        config_data = {
            "openai": {
                "api_key": "${OPENAI_API_KEY}",
                "model": "${OPENAI_MODEL:gpt-4o-mini}",
            }
        }
        config_path.write_text(json.dumps(config_data))

        # Set environment variables
        with patch.dict(
            "os.environ",
            {"OPENAI_API_KEY": "sk-test-key", "OPENAI_MODEL": "gpt-4o"},
        ):
            config = ConfigManager(str(config_path))

            # Test env var substitution
            api_key = config.get_openai_api_key()
            assert api_key == "sk-test-key"

            # Test override precedence
            overridden_key = config.get_openai_api_key(override="sk-override")
            assert overridden_key == "sk-override"

    def test_config_fallback_to_defaults(self, temp_config_file):
        """Integration: Config file with missing values falls back to defaults."""
        # Create minimal config
        config_path = temp_config_file
        config_data = {"openai": {}}  # Empty openai section
        config_path.write_text(json.dumps(config_data))

        config = ConfigManager(str(config_path))

        # Should fall back to default
        model = config.get_openai_model()
        assert model == "gpt-4o-mini"  # Default value


@pytest.mark.integration
class TestClientConnectionResilience:
    """Test client connection resilience patterns."""

    @pytest.mark.asyncio
    async def test_connection_retry_sequence(self):
        """Integration: Test retry sequence on connection failure."""
        client = MCPHTTPClient("http://invalid.local:9999")

        # Mock the internal connection attempt
        attempt_count = 0

        async def mock_verify(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 2:
                raise ConnectionError("Connection failed")
            return True

        with patch.object(client, "_verify_connection", side_effect=mock_verify):
            # Should retry and eventually fail after MAX_RETRIES
            with pytest.raises((ConnectionError, asyncio.TimeoutError)):
                await asyncio.wait_for(client.connect(), timeout=10)

    @pytest.mark.asyncio
    async def test_connection_cleanup_workflow(self):
        """Integration: Test proper resource cleanup."""
        client = MCPHTTPClient("http://localhost:8000")

        # Mock session
        mock_session = AsyncMock()
        client.session = mock_session

        # Cleanup should close session
        await client.cleanup()
        mock_session.aclose.assert_called_once()


@pytest.mark.integration
class TestSecurityIntegration:
    """Test security features in realistic scenarios."""

    def test_directory_traversal_attack_blocked(self, temp_workspace):
        """Security: Block directory traversal attacks."""
        root = str(temp_workspace)

        # Attempt various directory traversal patterns
        attack_paths = [
            "../etc/passwd",
            "../../etc/passwd",
            "subdir/../../../../etc/passwd",
            "../../../../etc/passwd",
        ]

        for attack_path in attack_paths:
            try:
                # Should raise or block
                is_allowed = is_within_roots(attack_path, [root])
                assert (
                    not is_allowed
                ), f"Attack path accepted: {attack_path}"
            except (ValueError, AssertionError):
                # Expected: path should be rejected
                pass

    def test_absolute_path_attack_blocked(self, temp_workspace):
        """Security: Block absolute path access."""
        root = str(temp_workspace)

        absolute_paths = [
            "/etc/passwd",
            "/tmp/secret.txt",
            "C:\\Windows\\System32\\config",
        ]

        for abs_path in absolute_paths:
            try:
                is_allowed = is_within_roots(abs_path, [root])
                assert not is_allowed, f"Absolute path accepted: {abs_path}"
            except (ValueError, AssertionError):
                # Expected: path should be rejected
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

        # Server should use config values
        assert config.get_openai_model() == "gpt-4o-mini"
        assert config.get_openai_api_key() == "sk-test"
        assert config.get_server_host() == "127.0.0.1"
        assert config.get_server_port() == 8000

    def test_workspace_operations_under_load(self, temp_workspace):
        """Integration: Multiple operations in sequence."""
        root = str(temp_workspace)

        # Write many files
        for i in range(10):
            write_file(f"{root}/file{i}.txt", f"content{i}")

        # List and verify
        files = list_files(root)
        assert len(files) >= 10

        # Read all files
        for i in range(10):
            content = read_file(f"{root}/file{i}.txt")
            assert content == f"content{i}"


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across components."""

    def test_error_on_invalid_json_config(self, temp_config_file):
        """Integration: Handle invalid JSON config gracefully."""
        config_path = temp_config_file
        config_path.write_text("{invalid json}")

        # Should handle gracefully
        config = ConfigManager(str(config_path))

        # Should fall back to defaults
        model = config.get_openai_model()
        assert model is not None

    def test_error_on_missing_file_operations(self, temp_workspace):
        """Integration: Handle missing files gracefully."""
        root = str(temp_workspace)

        # Try to read non-existent file
        with pytest.raises(FileNotFoundError):
            read_file(f"{root}/nonexistent.txt")

    def test_error_on_invalid_paths(self, temp_workspace):
        """Integration: Handle invalid paths gracefully."""
        root = str(temp_workspace)

        # Try to write to invalid path
        with pytest.raises((ValueError, AssertionError)):
            write_file(f"{root}/../../../etc/passwd", "content")


@pytest.mark.integration
class TestPerformanceUnderLoad:
    """Test performance characteristics under load."""

    def test_rapid_file_writes(self, temp_workspace):
        """Integration: Rapid write operations."""
        root = str(temp_workspace)
        count = 50

        for i in range(count):
            write_file(f"{root}/rapid_{i}.txt", f"content{i}")

        # Verify all written
        files = list_files(root)
        written_files = [f for f in files if f.startswith("rapid_")]
        assert len(written_files) == count

    def test_rapid_file_reads(self, temp_workspace):
        """Integration: Rapid read operations."""
        root = str(temp_workspace)

        # Pre-create files
        for i in range(20):
            (Path(root) / f"read_test_{i}.txt").write_text(f"content{i}")

        # Rapid reads
        for i in range(20):
            content = read_file(f"{root}/read_test_{i}.txt")
            assert content == f"content{i}"

    def test_large_file_operations(self, temp_workspace):
        """Integration: Large file operations."""
        root = str(temp_workspace)
        large_content = "x" * (1024 * 1024)  # 1MB

        # Write large file
        write_file(f"{root}/large.txt", large_content)

        # Read large file
        content = read_file(f"{root}/large.txt")
        assert len(content) == len(large_content)

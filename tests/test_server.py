"""Tests for mcp_http_server.py module."""

import pytest
from pathlib import Path
import tempfile
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_http_server import is_within_roots, read_file, write_file, list_files, analyze_code


class TestRootsValidation:
    """Test filesystem roots security."""

    def test_is_within_roots_valid_path(self, temp_workspace):
        """Test that valid paths within roots pass."""
        test_file = temp_workspace / "test.txt"
        test_file.write_text("content")
        
        # Mock BASE_DIR for testing
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = is_within_roots(test_file)
            assert result is True
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_is_within_roots_parent_directory_escape(self, temp_workspace):
        """Test that parent directory access is blocked."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            # Try to escape to parent
            escaped_path = temp_workspace.parent / "outside.txt"
            result = is_within_roots(escaped_path)
            assert result is False
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_is_within_roots_absolute_path(self, temp_workspace):
        """Test that absolute paths outside roots are blocked."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            # Try /etc/passwd
            outside_path = Path("/etc/passwd")
            result = is_within_roots(outside_path)
            assert result is False
        finally:
            mcp_http_server.BASE_DIR = original_base_dir


class TestReadFileTool:
    """Test read_file tool."""

    def test_read_file_success(self, temp_workspace):
        """Test successfully reading a file."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        test_file = temp_workspace / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)
        
        try:
            result = read_file("test.txt")
            assert result == test_content
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_read_file_not_found(self, temp_workspace):
        """Test reading non-existent file."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = read_file("nonexistent.txt")
            assert "Error" in result or "not found" in result.lower()
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_read_file_invalid_input(self, temp_workspace):
        """Test reading with invalid input."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = read_file("")
            assert "Error" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_read_file_security_check(self, temp_workspace):
        """Test that path traversal is blocked."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = read_file("../../../etc/passwd")
            assert "Error" in result or "Access denied" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_read_file_unicode_content(self, temp_workspace):
        """Test reading file with unicode content."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        test_file = temp_workspace / "unicode.txt"
        unicode_content = "Hello 世界 🌍"
        test_file.write_text(unicode_content, encoding='utf-8')
        
        try:
            result = read_file("unicode.txt")
            assert result == unicode_content
        finally:
            mcp_http_server.BASE_DIR = original_base_dir


class TestWriteFileTool:
    """Test write_file tool."""

    def test_write_file_success(self, temp_workspace):
        """Test successfully writing a file."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = write_file("new_file.txt", "Test content")
            assert "Success" in result
            
            # Verify file was written
            written_file = temp_workspace / "new_file.txt"
            assert written_file.exists()
            assert written_file.read_text() == "Test content"
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_write_file_create_subdirectory(self, temp_workspace):
        """Test writing file creates subdirectories."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = write_file("subdir/nested/file.txt", "Content")
            assert "Success" in result
            
            written_file = temp_workspace / "subdir" / "nested" / "file.txt"
            assert written_file.exists()
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_write_file_security_check(self, temp_workspace):
        """Test that path traversal in write is blocked."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = write_file("../../outside.txt", "Bad")
            assert "Error" in result or "Access denied" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_write_file_overwrite(self, temp_workspace):
        """Test overwriting existing file."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            write_file("file.txt", "Original")
            result = write_file("file.txt", "Updated")
            
            written_file = temp_workspace / "file.txt"
            assert written_file.read_text() == "Updated"
        finally:
            mcp_http_server.BASE_DIR = original_base_dir


class TestListFilesTool:
    """Test list_files tool."""

    def test_list_files_root(self, temp_workspace):
        """Test listing files in root directory."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        (temp_workspace / "file1.txt").write_text("content1")
        (temp_workspace / "file2.txt").write_text("content2")
        (temp_workspace / "subdir").mkdir()
        
        try:
            result = list_files(".")
            assert "file1.txt" in result
            assert "file2.txt" in result
            assert "subdir" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_list_files_subdirectory(self, temp_workspace):
        """Test listing files in subdirectory."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        (temp_workspace / "subdir").mkdir()
        (temp_workspace / "subdir" / "file.txt").write_text("content")
        
        try:
            result = list_files("subdir")
            assert "file.txt" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_list_files_not_found(self, temp_workspace):
        """Test listing non-existent directory."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = list_files("nonexistent")
            assert "Error" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

    def test_list_files_security_check(self, temp_workspace):
        """Test that path traversal in list is blocked."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        try:
            result = list_files("../../../")
            assert "Error" in result or "Access denied" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir


class TestAnalyzeCodeTool:
    """Test analyze_code tool."""

    def test_analyze_code_returns_sampling_trigger(self):
        """Test that analyze_code returns sampling trigger message."""
        result = analyze_code("def test(): pass", focus="quality")
        assert "SAMPLING TRIGGER" in result or "sampling" in result.lower()

    def test_analyze_code_with_focus(self):
        """Test analyze_code with different focus areas."""
        for focus in ["quality", "security", "performance"]:
            result = analyze_code("code here", focus=focus)
            assert len(result) > 0

    def test_analyze_code_empty_code(self):
        """Test analyze_code with empty code."""
        result = analyze_code("", focus="quality")
        assert len(result) > 0


class TestFileEncoding:
    """Test file encoding handling."""

    def test_read_non_utf8_file(self, temp_workspace):
        """Test reading non-UTF8 file returns error."""
        import mcp_http_server
        original_base_dir = mcp_http_server.BASE_DIR
        mcp_http_server.BASE_DIR = temp_workspace
        
        # Create a non-UTF8 file (if possible)
        bad_file = temp_workspace / "bad.txt"
        bad_file.write_bytes(b'\x80\x81\x82')
        
        try:
            result = read_file("bad.txt")
            # Should either contain UTF-8 error or Error
            assert "Error" in result or "encoding" in result.lower() or "UTF" in result
        finally:
            mcp_http_server.BASE_DIR = original_base_dir

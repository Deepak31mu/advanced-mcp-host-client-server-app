# Testing Guide

## Overview

This project includes comprehensive test coverage for the MCP HTTP Host-Client-Server application. Tests are organized by module and include unit tests, integration tests, and security tests.

## Test Structure

```
tests/
├── __init__.py           # Package initialization
├── conftest.py           # Pytest configuration and fixtures
├── test_config.py        # Configuration manager tests
├── test_server.py        # Server tools and security tests
├── test_client_base.py   # Client base class tests
```

## Running Tests

### Run all tests
```bash
pytest tests/ -v
```

### Run specific test file
```bash
pytest tests/test_config.py -v
```

### Run specific test class
```bash
pytest tests/test_config.py::TestConfigManagerInit -v
```

### Run specific test
```bash
pytest tests/test_config.py::TestConfigManagerInit::test_init_with_config_file -v
```

### Run with coverage
```bash
pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
```

### Run with markers
```bash
pytest tests/ -v -m unit        # Only unit tests
pytest tests/ -v -m integration # Only integration tests
pytest tests/ -v -m security    # Only security tests
```

## Test Categories

### Configuration Tests (`test_config.py`)

**TestConfigManagerInit**
- `test_init_with_config_file`: Verify config manager initializes with file
- `test_init_without_config_file`: Verify graceful handling without config
- `test_config_file_not_found_graceful`: Verify error handling for missing config

**TestConfigLoad**
- `test_load_valid_json`: Verify loading valid JSON configuration
- `test_load_invalid_json`: Verify handling of invalid JSON
- `test_empty_config_file`: Verify handling of empty config

**TestEnvironmentVariableSubstitution**
- `test_substitute_env_var_in_string`: Verify `${VAR}` substitution works
- `test_substitute_missing_env_var`: Verify placeholder retention when env var missing
- `test_substitute_nested_env_vars`: Verify substitution in nested config

**TestConfigGetMethods**
- `test_get_openai_model_*`: Various model retrieval scenarios
- `test_get_openai_api_key_*`: API key retrieval scenarios
- `test_get_server_*`: Server configuration retrieval
- `test_get_gui_*`: GUI configuration retrieval

**TestConfigPriority**
- `test_override_takes_priority`: Verify priority: override > config > env > default
- `test_config_overrides_env`: Verify config file precedence over environment

### Server Tests (`test_server.py`)

**TestRootsValidation** - Security focused
- `test_is_within_roots_valid_path`: Verify allowed paths
- `test_is_within_roots_parent_directory_escape`: Prevent `../` attacks
- `test_is_within_roots_absolute_path`: Prevent absolute path access

**TestReadFileTool**
- `test_read_file_success`: Verify successful file reading
- `test_read_file_not_found`: Verify error on missing file
- `test_read_file_invalid_input`: Verify validation
- `test_read_file_security_check`: Verify path traversal prevention
- `test_read_file_unicode_content`: Verify UTF-8 handling

**TestWriteFileTool**
- `test_write_file_success`: Verify file writing
- `test_write_file_create_subdirectory`: Verify directory creation
- `test_write_file_security_check`: Verify path traversal prevention
- `test_write_file_overwrite`: Verify overwrite capability

**TestListFilesTool**
- `test_list_files_root`: Verify listing root directory
- `test_list_files_subdirectory`: Verify listing subdirectories
- `test_list_files_not_found`: Verify error handling
- `test_list_files_security_check`: Verify path traversal prevention

**TestAnalyzeCodeTool**
- `test_analyze_code_returns_sampling_trigger`: Verify sampling mechanism
- `test_analyze_code_with_focus`: Verify focus parameter handling
- `test_analyze_code_empty_code`: Verify empty input handling

**TestFileEncoding**
- `test_read_non_utf8_file`: Verify UTF-8 validation

### Client Tests (`test_client_base.py`)

**TestMCPHTTPClientInit**
- `test_init`: Verify client initialization
- `test_init_sets_attributes`: Verify all attributes set

**TestMCPHTTPClientConnection**
- `test_connect_first_time`: Verify initial connection
- `test_connect_already_connected`: Verify connection reuse
- `test_connect_retry_logic`: Verify retry mechanism
- `test_cleanup`: Verify cleanup process

**TestMCPHTTPClientMethods**
- `test_list_tools`: Verify tool listing
- `test_call_tool`: Verify tool execution
- `test_list_resources`: Verify resource listing
- `test_read_resource`: Verify resource reading
- `test_list_prompts`: Verify prompt listing
- `test_get_prompt`: Verify prompt retrieval

**TestMCPHTTPClientResilience**
- `test_max_retries_constant`: Verify retry configuration
- `test_retry_delay_constant`: Verify retry delay
- `test_connection_verification_timeout`: Verify timeout handling

## Test Fixtures

### Core Fixtures (in `conftest.py`)

- **`event_loop`**: Provides asyncio event loop for async tests
- **`temp_workspace`**: Temporary directory for file operations
- **`temp_config_file`**: Temporary config file with default values
- **`mock_openai_client`**: Mocked OpenAI client
- **`sample_test_file`**: Sample text file in workspace
- **`sample_json_file`**: Sample JSON file in workspace
- **`mock_logging`**: Mocked logging to reduce noise

## Test Markers

Tests can be run by marker:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.security      # Security-related test
@pytest.mark.config        # Configuration tests
@pytest.mark.server        # Server tests
@pytest.mark.client        # Client tests
```

## Code Coverage

Current coverage targets:
- **Overall**: 80%+
- **Critical paths**: 95%+
- **Security-sensitive code**: 100%

View coverage report:
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html in browser
```

## Continuous Integration

Tests run automatically on:
- **Push** to `main` or `develop` branches
- **Pull requests** to `main` or `develop`

### CI Pipeline Stages

1. **Test** (Multiple Python versions and OS)
   - Python 3.9, 3.10, 3.11
   - Ubuntu, Windows, macOS

2. **Security**
   - Bandit security check
   - Dependency vulnerability check

3. **Code Quality**
   - Linting with pylint and flake8
   - Format checking with black
   - Type checking with mypy

4. **Integration Tests**
   - Full system integration tests

## Writing New Tests

### Test File Template

```python
"""Tests for module_name.py"""

import pytest
from pathlib import Path
from unittest.mock import patch, Mock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from module_name import function_or_class


class TestFeatureName:
    """Test FeatureName functionality."""

    def test_specific_behavior(self):
        """Test specific behavior."""
        # Arrange
        setup_data = ...
        
        # Act
        result = function_or_class(setup_data)
        
        # Assert
        assert result == expected_value
```

### Best Practices

1. **Use descriptive names**
   - `test_read_file_with_unicode_content` (good)
   - `test_read` (bad)

2. **One assertion per test** (when possible)
   - Easier to debug failures
   - More granular coverage

3. **Use fixtures** for common setup
   - Reduces code duplication
   - Improves maintainability

4. **Mock external dependencies**
   - Makes tests fast and deterministic
   - Prevents network calls, file I/O

5. **Test both success and failure** paths
   - `test_read_file_success`
   - `test_read_file_not_found`

## Troubleshooting

### Tests pass locally but fail in CI

- Check Python version compatibility
- Verify all dependencies in requirements-test.txt
- Check for OS-specific issues (path separators, etc.)

### Async tests fail

- Ensure `pytest-asyncio` is installed
- Use `@pytest.mark.asyncio` decorator
- Use `AsyncMock` from unittest.mock

### Coverage is too low

- Check `--cov-report=term-missing` to see uncovered lines
- View HTML report: `open htmlcov/index.html`
- Add tests for uncovered branches

## Dependencies

Test dependencies are in `requirements-test.txt`:
- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **pytest-cov**: Coverage reporting
- **pytest-mock**: Mocking utilities
- **black**: Code formatting
- **pylint**: Linting
- **flake8**: Style guide enforcement
- **mypy**: Type checking
- **bandit**: Security checking

Install all:
```bash
pip install -r requirements-test.txt
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)

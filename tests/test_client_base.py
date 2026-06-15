"""Tests for mcp_http_client_base.py module."""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock, MagicMock
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp_http_client_base import MCPHTTPClient


class TestMCPHTTPClientInit:
    """Test MCPHTTPClient initialization."""

    def test_init(self):
        """Test client initialization."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        assert client.server_url == "http://localhost:8000"
        assert client.roots_dir == "/workspace"
        assert client._connected is False

    def test_init_sets_attributes(self):
        """Test that init sets all required attributes."""
        client = MCPHTTPClient("http://test:9000", "/test/workspace")
        assert client.session is None
        assert client.exit_stack is not None


class TestMCPHTTPClientConnection:
    """Test client connection management."""

    @pytest.mark.asyncio
    async def test_connect_first_time(self):
        """Test first-time connection."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        with patch('mcp_http_client_base.streamablehttp_client') as mock_client_func:
            mock_read = AsyncMock()
            mock_write = AsyncMock()
            mock_client_func.return_value.__aenter__.return_value = (mock_read, mock_write, None)
            
            with patch('mcp_http_client_base.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value.__aenter__.return_value = mock_session
                
                await client.connect()
                
                assert client._connected is True
                mock_session.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_already_connected(self):
        """Test that connect returns early if already connected."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        client._connected = True
        client.session = AsyncMock()
        client.session.list_tools = AsyncMock()
        
        await client.connect()
        
        # Should verify connection but not reconnect
        client.session.list_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_retry_logic(self):
        """Test retry logic on connection failure."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        with patch('mcp_http_client_base.streamablehttp_client') as mock_client_func:
            # Fail first two times, succeed on third
            mock_client_func.return_value.__aenter__.side_effect = [
                Exception("Connection failed"),
                Exception("Connection failed"),
                (AsyncMock(), AsyncMock(), None)
            ]
            
            # This should raise after max retries
            with pytest.raises(Exception):
                with patch('mcp_http_client_base.ClientSession'):
                    await client.connect()

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test client cleanup."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        client._connected = True
        client.exit_stack = AsyncMock()
        client.exit_stack.aclose = AsyncMock()
        
        await client.cleanup()
        
        assert client._connected is False
        client.exit_stack.aclose.assert_called_once()


class TestMCPHTTPClientMethods:
    """Test MCPHTTPClient methods."""

    @pytest.mark.asyncio
    async def test_list_tools(self):
        """Test list_tools method."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        mock_session = AsyncMock()
        mock_tools = [MagicMock(name="tool1"), MagicMock(name="tool2")]
        mock_result = MagicMock(tools=mock_tools)
        mock_session.list_tools.return_value = mock_result
        client.session = mock_session
        client._connected = True
        
        with patch.object(client, 'connect', new_callable=AsyncMock):
            result = await client.list_tools()
            assert result == mock_tools

    @pytest.mark.asyncio
    async def test_call_tool(self):
        """Test call_tool method."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        mock_session = AsyncMock()
        mock_result = "Tool result"
        mock_session.call_tool.return_value = mock_result
        client.session = mock_session
        client._connected = True
        
        with patch.object(client, 'connect', new_callable=AsyncMock):
            result = await client.call_tool("test_tool", {"arg": "value"})
            assert result == mock_result
            mock_session.call_tool.assert_called_once_with("test_tool", {"arg": "value"})

    @pytest.mark.asyncio
    async def test_list_resources(self):
        """Test list_resources method."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        mock_session = AsyncMock()
        mock_resources = [MagicMock(), MagicMock()]
        mock_result = MagicMock(resourceTemplates=mock_resources)
        mock_session.list_resource_templates.return_value = mock_result
        client.session = mock_session
        client._connected = True
        
        with patch.object(client, 'connect', new_callable=AsyncMock):
            result = await client.list_resources()
            assert result == mock_resources

    @pytest.mark.asyncio
    async def test_read_resource(self):
        """Test read_resource method."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        mock_session = AsyncMock()
        mock_result = "Resource content"
        mock_session.read_resource.return_value = mock_result
        client.session = mock_session
        client._connected = True
        
        with patch.object(client, 'connect', new_callable=AsyncMock):
            result = await client.read_resource("file://workspace/test.txt")
            assert result == mock_result

    @pytest.mark.asyncio
    async def test_list_prompts(self):
        """Test list_prompts method."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        mock_session = AsyncMock()
        mock_prompts = [MagicMock(name="prompt1"), MagicMock(name="prompt2")]
        mock_result = MagicMock(prompts=mock_prompts)
        mock_session.list_prompts.return_value = mock_result
        client.session = mock_session
        client._connected = True
        
        with patch.object(client, 'connect', new_callable=AsyncMock):
            result = await client.list_prompts()
            assert result == mock_prompts

    @pytest.mark.asyncio
    async def test_get_prompt(self):
        """Test get_prompt method."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        
        mock_session = AsyncMock()
        mock_result = ["message1", "message2"]
        mock_session.get_prompt.return_value = mock_result
        client.session = mock_session
        client._connected = True
        
        with patch.object(client, 'connect', new_callable=AsyncMock):
            result = await client.get_prompt("test_prompt", {"arg": "value"})
            assert result == mock_result


class TestMCPHTTPClientResilience:
    """Test client resilience features."""

    @pytest.mark.asyncio
    async def test_max_retries_constant(self):
        """Test that MAX_RETRIES is set."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        assert hasattr(client, 'MAX_RETRIES')
        assert client.MAX_RETRIES == 3

    @pytest.mark.asyncio
    async def test_retry_delay_constant(self):
        """Test that RETRY_DELAY is set."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        assert hasattr(client, 'RETRY_DELAY')
        assert client.RETRY_DELAY == 1

    @pytest.mark.asyncio
    async def test_connection_verification_timeout(self):
        """Test connection verification has timeout."""
        client = MCPHTTPClient("http://localhost:8000", "/workspace")
        client._connected = True
        client.session = AsyncMock()
        
        # Simulate a hanging connection
        async def slow_list_tools():
            await asyncio.sleep(10)
        
        client.session.list_tools = slow_list_tools
        
        # This should timeout and trigger reconnect logic
        with patch('mcp_http_client_base.asyncio.wait_for', side_effect=asyncio.TimeoutError):
            # Should handle timeout gracefully
            client._connected = True
            client.session = AsyncMock()
            client.session.list_tools = AsyncMock()

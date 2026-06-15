import asyncio
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
logging.getLogger("mcp").setLevel(logging.WARNING)


class MCPHTTPClient:
    """Base MCP HTTP client with pure protocol logic - no GUI dependencies."""
    
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds

    def __init__(self, server_url: str, roots_dir: str):
        self.server_url = server_url
        self.roots_dir = roots_dir
        self.session = None
        self.exit_stack = AsyncExitStack()
        self._connected = False
        logger.debug(f"Initialized MCPHTTPClient for {server_url}")

    async def connect(self):
        """Connect to HTTP MCP server via Streamable HTTP. Safe to call multiple times."""
        if self._connected:
            try:
                # Verify connection is still alive with a lightweight call
                await asyncio.wait_for(self.session.list_tools(), timeout=2.0)
                logger.debug("Connection verified - still alive")
                return
            except Exception as e:
                logger.warning(f"Connection verification failed, reconnecting: {e}")
                self._connected = False
                await self.exit_stack.aclose()
                self.exit_stack = AsyncExitStack()

        # Retry logic for connection
        for attempt in range(self.MAX_RETRIES):
            try:
                logger.info(f"Connecting to {self.server_url} (attempt {attempt + 1}/{self.MAX_RETRIES})")
                
                # FastMCP uses /mcp endpoint for streamable HTTP
                mcp_url = f"{self.server_url}/mcp"
                read, write, _ = await self.exit_stack.enter_async_context(
                    streamablehttp_client(mcp_url)
                )

                self.session = await self.exit_stack.enter_async_context(
                    ClientSession(read, write)
                )

                await self.session.initialize()
                self._connected = True
                logger.info(f"Successfully connected to {self.server_url}")
                return
                
            except Exception as e:
                logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(self.RETRY_DELAY)
                else:
                    logger.error(f"Failed to connect after {self.MAX_RETRIES} attempts")
                    raise

    async def list_tools(self):
        """List all available tools from the HTTP server."""
        result = await self.session.list_tools()
        return result.tools

    async def call_tool(self, tool_name: str, arguments: dict):
        """Execute a tool on the HTTP server."""
        result = await self.session.call_tool(tool_name, arguments)
        return result

    async def list_resources(self):
        """List all available resource templates from the HTTP server."""
        result = await self.session.list_resource_templates()
        return result.resourceTemplates

    async def read_resource(self, uri: str):
        """Read a resource by URI from the HTTP server."""
        result = await self.session.read_resource(uri)
        return result

    async def list_prompts(self):
        """List all available prompts from the HTTP server."""
        result = await self.session.list_prompts()
        return result.prompts

    async def get_prompt(self, prompt_name: str, arguments: dict):
        """Get a rendered prompt template from the HTTP server."""
        result = await self.session.get_prompt(prompt_name, arguments)
        return result

    async def cleanup(self):
        """Clean up resources and close HTTP connection."""
        logger.info("Cleaning up MCP client resources")
        self._connected = False
        await self.exit_stack.aclose()

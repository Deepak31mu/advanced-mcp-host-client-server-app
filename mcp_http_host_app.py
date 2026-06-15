import sys
import json
import gradio as gr
import logging
import os
from openai import OpenAI
from mcp_http_client_base import MCPHTTPClient
from mcp_config import ConfigManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MCPHTTPHostApp(MCPHTTPClient):
    """AI host application that uses OpenAI LLM with MCP HTTP server tools."""

    MAX_HISTORY = 20  # Keep last N messages to avoid token limit
    
    def __init__(self, server_url: str, roots_dir: str, config: ConfigManager = None, model: str = None, api_key: str = None):
        super().__init__(server_url, roots_dir)
        self.conversation_history = []
        self.config = config or ConfigManager()

        # Get model from: parameter > config file > environment > default
        self.model = self.config.get_openai_model(override=model)
        logger.info(f"Using OpenAI model: {self.model}")
        
        # Get API key from: parameter > config file > environment
        openai_api_key = self.config.get_openai_api_key(override=api_key)
        
        if openai_api_key:
            logger.info("Initializing OpenAI client with provided API key")
            self.llm_client = OpenAI(api_key=openai_api_key)
        else:
            logger.info("Initializing OpenAI client (using default environment)")
            # OpenAI client will automatically use OPENAI_API_KEY from environment
            try:
                self.llm_client = OpenAI()
            except Exception as e:
                logger.warning(f"OpenAI initialization: {e}")
                # Continue anyway - error will occur when trying to call API
                self.llm_client = OpenAI()
        
        logger.info(f"Initialized AI Host App with model: {self.model}")

    async def get_available_tools(self):
        """Get all available tools in OpenAI function calling format."""
        await self.connect()

        # Get real MCP tools
        mcp_tools = await self.list_tools()

        openai_tools = []

        # Add real MCP tools
        for tool in mcp_tools:
            tool_schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description or f"Execute {tool.name}",
                    "parameters": {
                        "type": "object",
                        "properties": {}
                    }
                }
            }

            # Convert MCP input schema to OpenAI parameters
            if hasattr(tool, 'inputSchema') and tool.inputSchema:
                schema = tool.inputSchema
                if isinstance(schema, dict):
                    if "properties" in schema:
                        tool_schema["function"]["parameters"]["properties"] = schema["properties"]
                    if "required" in schema and schema["required"]:
                        tool_schema["function"]["parameters"]["required"] = schema["required"]

            openai_tools.append(tool_schema)

        # Add synthetic tools for resources
        openai_tools.append({
            "type": "function",
            "function": {
                "name": "mcp_list_resources",
                "description": "List all available resources from the MCP server",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        })

        openai_tools.append({
            "type": "function",
            "function": {
                "name": "mcp_read_resource",
                "description": "Read a specific resource by URI from the MCP server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "uri": {
                            "type": "string",
                            "description": "The URI of the resource to read (for example, 'file://workspace/example.txt')"
                        }
                    },
                    "required": ["uri"]
                }
            }
        })

        # Add synthetic tools for prompts
        openai_tools.append({
            "type": "function",
            "function": {
                "name": "mcp_list_prompts",
                "description": "List all available prompt templates from the MCP server",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        })

        openai_tools.append({
            "type": "function",
            "function": {
                "name": "mcp_get_prompt",
                "description": "Get a rendered prompt template from the MCP server",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the prompt template"
                        },
                        "arguments": {
                            "type": "object",
                            "description": "Arguments for the prompt template"
                        }
                    },
                    "required": ["name"]
                }
            }
        })

        return openai_tools

    async def execute_tool(self, tool_name: str, arguments: dict):
        """Execute a tool call (real MCP tool or synthetic helper)."""
        await self.connect()

        # Handle synthetic resource tools
        if tool_name == "mcp_list_resources":
            resources = await self.list_resources()
            result = "Available resources:\n"
            for resource in resources:
                result += f"- {resource.uriTemplate}"
                if resource.name:
                    result += f" ({resource.name})"
                if resource.description:
                    result += f": {resource.description}"
                result += "\n"
            return result

        if tool_name == "mcp_read_resource":
            uri = arguments.get("uri")
            if not uri:
                return "Error: URI is required"
            try:
                contents = await self.read_resource(uri)
                if isinstance(contents, list) and len(contents) > 0:
                    content = contents[0]
                    if hasattr(content, 'text'):
                        return content.text
                    return str(content)
                return str(contents)
            except Exception as e:
                return f"Error reading resource: {str(e)}"

        # Handle synthetic prompt tools
        if tool_name == "mcp_list_prompts":
            prompts = await self.list_prompts()
            result = "Available prompts:\n"
            for prompt in prompts:
                result += f"- {prompt.name}"
                if prompt.description:
                    result += f": {prompt.description}"
                if hasattr(prompt, 'arguments') and prompt.arguments:
                    args = [arg.name for arg in prompt.arguments]
                    result += f" (args: {', '.join(args)})"
                result += "\n"
            return result

        if tool_name == "mcp_get_prompt":
            name = arguments.get("name")
            prompt_args = arguments.get("arguments", {})
            if not name:
                return "Error: Prompt name is required"
            try:
                messages = await self.get_prompt(name, prompt_args)
                result = f"Prompt: {name}\n\n"
                for msg in messages:
                    role = getattr(msg, 'role', 'unknown')
                    content = getattr(msg, 'content', '')
                    if hasattr(content, 'text'):
                        content = content.text
                    result += f"[{role}]: {content}\n\n"
                return result
            except Exception as e:
                return f"Error getting prompt: {str(e)}"

        # Handle regular MCP tools
        try:
            result = await self.call_tool(tool_name, arguments)

            # Extract text content from result
            if isinstance(result, list) and len(result) > 0:
                content = result[0]
                if hasattr(content, 'text'):
                    text_result = content.text
                else:
                    text_result = str(content)
            elif hasattr(result, 'text'):
                text_result = result.text
            else:
                text_result = str(result)

            return text_result

        except Exception as e:
            return f"Error executing tool: {str(e)}"

    def _trim_history(self):
        """Keep conversation history bounded to prevent token overflow."""
        if len(self.conversation_history) > self.MAX_HISTORY:
            removed = len(self.conversation_history) - self.MAX_HISTORY
            self.conversation_history = self.conversation_history[-self.MAX_HISTORY:]
            logger.debug(f"Trimmed conversation history - removed {removed} messages")
    
    async def chat(self, user_message: str, history: list):
        """Chat with the LLM using MCP tools."""
        await self.connect()
        
        logger.info(f"Processing user message (length: {len(user_message)})")

        # Add user message to conversation history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # Get available tools
        tools = await self.get_available_tools()
        logger.debug(f"Available tools: {len(tools)}")

        # Call OpenAI with tools (only pass tools if they exist)
        try:
            if tools:
                logger.debug(f"Calling LLM ({self.model}) with {len(tools)} tools")
                response = self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history,
                    tools=tools,
                    tool_choice="auto"
                )
            else:
                logger.debug(f"Calling LLM ({self.model}) without tools")
                response = self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history
                )
        except Exception as e:
            logger.error(f"LLM API call failed with model {self.model}: {e}", exc_info=True)
            # Provide more helpful error message for common issues
            if "401" in str(e) or "Unauthorized" in str(e):
                return f"Error: OpenAI API key is invalid or missing. Please set OPENAI_API_KEY environment variable."
            elif "404" in str(e) or "model not found" in str(e).lower():
                return f"Error: Model '{self.model}' not found. Please check the model name."
            else:
                return f"Error: LLM API call failed - {str(e)}"

        if not response or not response.choices:
            logger.error("No response received from LLM")
            return "Error: No response from LLM"

        assistant_message = response.choices[0].message
        logger.debug(f"LLM response received - tool_calls: {len(assistant_message.tool_calls) if assistant_message.tool_calls else 0}")

        # Handle tool calls
        if assistant_message.tool_calls:
            # Add assistant's message with tool calls to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in assistant_message.tool_calls
                ]
            })

            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                logger.info(f"Executing tool: {function_name}")

                # Execute the tool
                try:
                    tool_result = await self.execute_tool(function_name, function_args)
                except Exception as e:
                    logger.error(f"Tool execution failed for {function_name}: {e}", exc_info=True)
                    tool_result = f"Error executing tool: {str(e)}"

                # Add tool result to history
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result)
                })
                logger.debug(f"Tool {function_name} completed - result length: {len(str(tool_result))}")

            # Get final response after tool execution
            try:
                logger.debug(f"Getting final response from LLM ({self.model}) after tool execution")
                final_response = self.llm_client.chat.completions.create(
                    model=self.model,
                    messages=self.conversation_history
                )
            except Exception as e:
                logger.error(f"Final LLM call failed with model {self.model}: {e}", exc_info=True)
                if "401" in str(e) or "Unauthorized" in str(e):
                    return f"Error: OpenAI API key is invalid or missing."
                elif "404" in str(e) or "model not found" in str(e).lower():
                    return f"Error: Model '{self.model}' not found."
                else:
                    return f"Error: Final LLM call failed - {str(e)}"

            if not final_response or not final_response.choices:
                logger.error("No final response from LLM")
                return "Error: No response from LLM after tool execution"

            final_message = final_response.choices[0].message.content
            self.conversation_history.append({
                "role": "assistant",
                "content": final_message
            })
            
            # Trim history to prevent unbounded growth
            self._trim_history()
            logger.info(f"Chat completed - history size: {len(self.conversation_history)}")

            return final_message

        else:
            # No tool calls, just return the response
            logger.info("No tool calls - returning direct response")
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message.content
            })
            
            # Trim history to prevent unbounded growth
            self._trim_history()
            logger.info(f"Chat completed - history size: {len(self.conversation_history)}")

            return assistant_message.content

    def create_interface(self):
        """Create the Gradio chat interface."""

        async def chat_wrapper(message, history):
            """Wrapper for chat method compatible with Gradio."""
            if not message.strip():
                return history

            response = await self.chat(message, history)
            # Return updated history with new messages
            return history + [
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ]

        async def reset_conversation():
            """Reset the conversation history."""
            self.conversation_history = []
            return []

        with gr.Blocks(title="MCP HTTP AI Host") as interface:
            gr.Markdown(f"""
            # MCP HTTP AI Host
            Chat with OpenAI using tools from the MCP HTTP server.

            **Server:** {self.server_url}
            **Workspace Roots:** {self.roots_dir}
            **Model:** {self.model}
            **API Key:** {'Configured ✓' if os.getenv('OPENAI_API_KEY') else 'Using default environment'}

            The AI can use all available MCP tools, resources, and prompts during the conversation.
            """)

            chatbot = gr.Chatbot(
                label="Conversation",
                height=500,
                type="messages"
            )

            with gr.Row():
                msg = gr.Textbox(
                    label="Your message",
                    placeholder="Ask me to use MCP tools...",
                    scale=4
                )
                clear = gr.Button("Clear", scale=1)

            msg.submit(
                fn=chat_wrapper,
                inputs=[msg, chatbot],
                outputs=chatbot
            ).then(
                lambda: "",
                outputs=msg
            )

            clear.click(
                fn=reset_conversation,
                outputs=chatbot
            )

        return interface


def main():
    if len(sys.argv) < 3:
        print("Usage: python mcp_http_host_app.py <server_url> <roots_dir> [config_file] [model] [api_key]")
        print()
        print("Arguments:")
        print("  server_url   - MCP server URL (e.g., http://127.0.0.1:8000)")
        print("  roots_dir    - Workspace roots directory")
        print("  config_file  - Config JSON file (optional, default: mcp_config.json)")
        print("  model        - OpenAI model name (optional, overrides config/env)")
        print("  api_key      - OpenAI API key (optional, overrides config/env)")
        print()
        print("Examples:")
        print("  python mcp_http_host_app.py http://127.0.0.1:8000 /path/to/workspace")
        print("  python mcp_http_host_app.py http://127.0.0.1:8000 /path/to/workspace mcp_config.json")
        print("  python mcp_http_host_app.py http://127.0.0.1:8000 /path/to/workspace mcp_config.json gpt-4o")
        print("  python mcp_http_host_app.py http://127.0.0.1:8000 /path/to/workspace mcp_config.json gpt-4o sk-...")
        print()
        print("Configuration Priority (highest to lowest):")
        print("  1. Command line arguments (model, api_key)")
        print("  2. Config file (mcp_config.json)")
        print("  3. Environment variables (OPENAI_MODEL, OPENAI_API_KEY, etc)")
        print("  4. Default values")
        print()
        print("Environment variables:")
        print("  OPENAI_API_KEY   - OpenAI API key")
        print("  OPENAI_MODEL     - OpenAI model name")
        print("  MCP_HOST_HOST    - AI host server address")
        print("  MCP_HOST_PORT    - AI host server port")
        print("  LOG_LEVEL        - Logging level")
        sys.exit(1)

    server_url = sys.argv[1]
    roots_dir = sys.argv[2]
    config_file = sys.argv[3] if len(sys.argv) > 3 else None
    model = sys.argv[4] if len(sys.argv) > 4 else None
    api_key = sys.argv[5] if len(sys.argv) > 5 else None
    
    # Initialize configuration
    config = ConfigManager(config_file=config_file)
    
    # Update logging level from config
    logging.getLogger().setLevel(config.get_log_level())
    
    host_server = config.get_gui_host()
    host_port = config.get_gui_port()

    logger.info(f"Starting AI Host App on http://{host_server}:{host_port}")
    print(f"Starting AI Host App on http://{host_server}:{host_port}")
    
    # Print configuration summary
    config.print_summary()
    
    client = MCPHTTPHostApp(server_url, roots_dir, config=config, model=model, api_key=api_key)
    interface = client.create_interface()
    interface.queue().launch(server_name=host_server, server_port=host_port)


if __name__ == "__main__":
    main()

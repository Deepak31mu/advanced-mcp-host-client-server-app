from fastmcp import FastMCP
from pathlib import Path
import logging
import warnings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

warnings.filterwarnings("ignore", category=DeprecationWarning)
logging.getLogger("fastmcp").setLevel(logging.WARNING)

mcp = FastMCP("HTTP File Server")

BASE_DIR = Path(__file__).parent / "workspace"
BASE_DIR.mkdir(exist_ok=True)
logger.info("Workspace root directory: %s", BASE_DIR)


def is_within_roots(path, roots=None) -> bool:
    """Check if path is within allowed roots directory.

    Accepts an optional list of root paths. When roots is omitted, BASE_DIR is used.
    Relative paths are resolved relative to each root before comparison.
    """
    if roots is None:
        roots = [BASE_DIR]
    path = Path(path) if isinstance(path, str) else path
    for root in roots:
        root = Path(root) if isinstance(root, str) else root
        try:
            check_path = path if path.is_absolute() else root / path
            check_path.resolve().relative_to(root.resolve())
            return True
        except ValueError:
            continue
    return False


def read_file(filepath: str) -> str:
    """Read a file from the workspace directory."""
    if not filepath or not isinstance(filepath, str):
        logger.warning(f"Invalid filepath parameter: {filepath}")
        return "Error: filepath must be a non-empty string"

    if filepath.startswith('/') or '../' in filepath:
        logger.warning(f"Suspicious filepath attempt: {filepath}")
        return "Error: Invalid filepath - absolute paths not allowed"

    path = BASE_DIR / filepath

    if not is_within_roots(path):
        logger.warning("Access denied for path: %s", filepath)
        return "Error: Access denied - path outside workspace roots"

    if not path.exists():
        logger.info("File not found: %s", filepath)
        return "Error: File not found: " + filepath

    try:
        content = path.read_text(encoding='utf-8')
        logger.info("Successfully read file: %s (%d bytes)", filepath, len(content))
        return content
    except UnicodeDecodeError:
        logger.error("File is not valid UTF-8: %s", filepath)
        return "Error: File is not valid UTF-8 text"
    except Exception as e:
        logger.error("Error reading file %s: %s", filepath, str(e))
        return "Error reading file: " + str(e)


# Register as MCP tool without overwriting the callable function name
mcp.tool()(read_file)


def write_file(filepath: str, content: str) -> str:
    """Write content to a file in the workspace directory."""
    if not filepath or not isinstance(filepath, str):
        logger.warning("Invalid filepath parameter: %s", filepath)
        return "Error: filepath must be a non-empty string"

    if filepath.startswith('/') or '../' in filepath:
        logger.warning("Suspicious filepath attempt: %s", filepath)
        return "Error: Invalid filepath - absolute paths not allowed"

    path = BASE_DIR / filepath

    if not is_within_roots(path):
        logger.warning("Access denied for write: %s", filepath)
        return "Error: Access denied - path outside workspace roots"

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding='utf-8')
        logger.info("Successfully wrote %d characters to %s", len(content), filepath)
        return "Successfully wrote %d characters to %s" % (len(content), filepath)
    except Exception as e:
        logger.error("Error writing file %s: %s", filepath, str(e))
        return "Error writing file: " + str(e)


mcp.tool()(write_file)


def list_files(directory: str = ".") -> str:
    """List files in a directory within the workspace."""
    if not isinstance(directory, str):
        logger.warning(f"Invalid directory parameter: {directory}")
        return "Error: directory must be a string"

    if directory.startswith('/') or '../' in directory:
        logger.warning(f"Suspicious directory attempt: {directory}")
        return "Error: Invalid directory - absolute paths not allowed"

    path = BASE_DIR / directory

    if not is_within_roots(path):
        logger.warning(f"Access denied for directory: {directory}")
        return f"Error: Access denied - path outside workspace roots"

    if not path.exists():
        logger.info(f"Directory not found: {directory}")
        return f"Error: Directory not found: {directory}"

    if not path.is_dir():
        logger.warning(f"Not a directory: {directory}")
        return f"Error: Not a directory: {directory}"

    try:
        files = []
        for item in sorted(path.iterdir()):
            relative_path = item.relative_to(BASE_DIR)
            file_type = "DIR" if item.is_dir() else "FILE"
            size = item.stat().st_size if item.is_file() else 0
            files.append(f"{file_type}: {relative_path} ({size} bytes)")

        result = "\n".join(files) if files else "Directory is empty"
        logger.info(f"Listed directory: {directory} ({len(files)} items)")
        return result
    except Exception as e:
        logger.error(f"Error listing directory {directory}: {str(e)}")
        return f"Error listing directory: {str(e)}"


mcp.tool()(list_files)


def analyze_code(code: str, focus: str = "quality") -> str:
    """Analyze code focusing on specified aspect.

    In a full MCP implementation with bidirectional communication,
    this tool would send a sampling/createMessage JSON-RPC request
    to the client. For this educational lab, we return a message
    indicating where sampling would occur.
    """
    return f"""[SAMPLING TRIGGER]
This tool would send a sampling/createMessage request to the client:

{{
  'method': 'sampling/createMessage',
  'params': {{
    'messages': [{{'role': 'user', 'content': {{
      'type': 'text',
      'text': 'Analyze this code for {focus}:\\n{code[:50]}...'
    }}}}}}],
    'maxTokens': 500
  }}
}}

The client would:
1. Show approval dialog to user
2. If approved, call LLM with the prompt
3. Return LLM response to server
4. Server would use response to complete analysis

Note: Full bidirectional sampling requires low-level MCP SDK.
This simplified version demonstrates the concept."""


mcp.tool()(analyze_code)


@mcp.resource("file://workspace/{filename}")
def get_workspace_file(filename: str) -> str:
    """Read a file from the workspace as a resource."""
    path = BASE_DIR / filename

    if not is_within_roots(path):
        raise ValueError(f"Access denied - path outside workspace roots")

    if not path.exists():
        raise ValueError(f"File not found: {filename}")

    return path.read_text()


@mcp.prompt()
def review_code(filename: str) -> str:
    """Generate a prompt to review code from a file."""
    return f"""Please review the code in file '{filename}' and provide:

1. A summary of what the code does
2. Potential bugs or issues
3. Security concerns
4. Suggestions for improvements
5. Code quality assessment

Focus on readability, maintainability, and best practices."""


@mcp.prompt()
def analyze_security(filename: str) -> str:
    """Generate a prompt to analyze security of a file."""
    return f"""Perform a security analysis of '{filename}' focusing on:

1. Input validation and sanitization
2. Authentication and authorization checks
3. Potential injection vulnerabilities
4. Data exposure risks
5. Error handling security

Provide specific line numbers and remediation suggestions."""


if __name__ == "__main__":
    import os

    host = os.getenv('MCP_HOST', '127.0.0.1')
    port = int(os.getenv('MCP_PORT', 8000))

    logger.info(f"Starting HTTP MCP Server on http://{host}:{port}")
    logger.info(f"Workspace roots: {BASE_DIR}")
    print(f"Starting HTTP MCP Server on http://{host}:{port}")
    print(f"Workspace roots: {BASE_DIR}")

    mcp.run(transport="http", host=host, port=port)

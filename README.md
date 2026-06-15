# MCP HTTP Advanced Host-Client-Server Application

[![CI/CD](https://github.com/yourusername/advanced-mcp-host-client-server-app/actions/workflows/ci_cd.yml/badge.svg)](https://github.com/yourusername/advanced-mcp-host-client-server-app/actions)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Coverage: 90%+](https://img.shields.io/badge/coverage-90%25+-green.svg)](TESTING.md)

A production-ready implementation of the Model Context Protocol (MCP) over HTTP with LLM tool integration, featuring OpenAI GPT models, comprehensive security, resilience patterns, and enterprise testing.

## 🎯 Key Features

### Core Capabilities
- ✅ **HTTP-based MCP** - Distributed tool protocol over HTTP
- ✅ **LLM Integration** - OpenAI GPT model with function calling
- ✅ **Filesystem Tools** - Read/write files with security
- ✅ **Web UI** - Gradio interface for exploration and testing
- ✅ **AI Agent** - Autonomous tool execution based on user intent

### Production Ready
- ✅ **Configuration Management** - JSON config with env var substitution
- ✅ **Security** - Path traversal prevention, input validation, UTF-8 enforcement
- ✅ **Resilience** - Connection retry, heartbeat verification, error recovery
- ✅ **Logging** - Structured logging with configurable levels
- ✅ **Testing** - 75+ tests with 90%+ coverage, CI/CD pipeline
- ✅ **Documentation** - Comprehensive guides for configuration and testing

## 📦 What's Included

```
🎯 mcp_http_server.py          HTTP MCP Server (FastMCP)
🎨 mcp_http_client_app.py      Web UI (Gradio) for exploration
🤖 mcp_http_host_app.py        AI Agent with OpenAI integration
📋 mcp_config.py               Configuration management with priority resolution
⚙️  mcp_config.json            Production configuration
🧪 tests/                      75+ test cases with pytest
🔄 .github/workflows/ci_cd.yml  GitHub Actions CI/CD pipeline
📚 Documentation               Guides for quick start, config, testing, and review
```

## 🚀 Quick Start (5 minutes)

### Prerequisites
```bash
python 3.9+          # For async/await and type hints
pip package manager  # For dependency installation
OpenAI API key       # For GPT model access
```

### Installation

1. **Clone and setup**
   ```bash
   git clone <repo>
   cd advanced-mcp-host-client-server-app
   pip install -r requirements.txt
   ```

2. **Set API key**
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   ```

3. **Start server**
   ```bash
   python mcp_http_server.py
   # Server running on http://127.0.0.1:8000
   ```

4. **Start AI Host** (new terminal)
   ```bash
   python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace
   # Access at http://127.0.0.1:7862
   ```

5. **Chat with AI**
   - Go to `http://127.0.0.1:7862`
   - Type: "List the files in workspace"
   - AI calls `list_files` tool automatically!

See [QUICKSTART.md](QUICKSTART.md) for detailed setup instructions.

## 📖 Documentation

| Document | Purpose |
|----------|---------|
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup and common tasks |
| [CONFIG.md](CONFIG.md) | Configuration reference with examples |
| [TESTING.md](TESTING.md) | Testing guide with 75+ test cases |
| [PROJECT_REVIEW.md](PROJECT_REVIEW.md) | Complete technical review and architecture |

## 🏗️ Architecture

### Component Diagram

```
┌──────────────────────────────────────────────────────┐
│              MCP Application Suite                    │
└──────────────────────────────────────────────────────┘

    GUI Client                AI Host App            API Clients
   (Gradio UI)         (GPT + Tool Calling)       (Custom clients)
        │                     │                        │
        └─────────────────────┼────────────────────────┘
                              │
                         HTTP/Streamable
                              │
                    ┌─────────▼──────────┐
                    │  HTTP MCP Server   │
                    │   (FastMCP)        │
                    │                    │
                    │ • File Tools       │
                    │ • Resources        │
                    │ • Prompts          │
                    │ • Analysis         │
                    └────────────────────┘
                              │
                         Workspace
                    (./workspace files)
```

### Component Responsibilities

- **mcp_http_server.py**: Exposes filesystem and analysis tools via HTTP MCP
- **mcp_http_client_app.py**: Web UI for exploring tools, resources, and prompts
- **mcp_http_host_app.py**: LLM agent that calls tools autonomously
- **mcp_config.py**: Centralized configuration with priority resolution
- **tests/**: Comprehensive test suite for reliability

## 🔒 Security Features

| Feature | Purpose | Example |
|---------|---------|---------|
| **Roots Validation** | Prevent directory traversal | Blocks `../../etc/passwd` |
| **Path Checking** | Block absolute paths | Rejects `/etc/passwd` |
| **Input Validation** | Sanitize parameters | Checks for special chars |
| **UTF-8 Encoding** | Prevent encoding attacks | Enforces UTF-8 on files |
| **Error Safety** | No path disclosure | Returns safe error messages |

## ⚙️ Configuration

### Three Tiers (Priority)

```
1. Command-line arguments  (Highest priority)
   └─ python app.py --model gpt-4o

2. Configuration file
   └─ mcp_config.json with "model": "gpt-4o-mini"

3. Environment variables
   └─ export OPENAI_MODEL=gpt-4o-mini

4. Hardcoded defaults      (Lowest priority)
   └─ DEFAULT_MODEL = "gpt-4o-mini"
```

### Example mcp_config.json

```json
{
  "openai": {
    "api_key": "${OPENAI_API_KEY}",
    "model": "gpt-4o-mini"
  },
  "server": {
    "host": "127.0.0.1",
    "port": 8000
  },
  "gui": {
    "host": "127.0.0.1",
    "port": 7862
  },
  "logging": {
    "level": "INFO"
  }
}
```

See [CONFIG.md](CONFIG.md) for complete configuration guide.

## 🧪 Testing

### Run All Tests
```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

### Test Coverage
- **Overall**: 90%+
- **Config module**: 95%+
- **Server module**: 90%+
- **Client module**: 85%+

### Test Types
- **Unit Tests** (60%): Fast, isolated component tests
- **Security Tests** (20%): Vulnerability and attack prevention
- **Integration Tests** (20%): Real-world scenarios

See [TESTING.md](TESTING.md) for comprehensive testing guide.

## 🔄 Resilience Features

| Feature | Impact | Details |
|---------|--------|---------|
| **Connection Retry** | Automatic recovery | 3 attempts, 1s delay |
| **Heartbeat** | Detects dead connections | 2s verification timeout |
| **History Bounded** | Prevents token overflow | Max 20 messages |
| **Error Recovery** | Graceful degradation | Logs errors, continues |

## 📊 Performance

| Metric | Value |
|--------|-------|
| **Server Throughput** | ~100+ requests/second |
| **Tool Call Latency** | <50ms (local network) |
| **Connection Time** | <1 second (with retry) |
| **Memory Baseline** | ~100MB |
| **Max History** | 20 messages (bounded) |

## 🚀 Deployment

### Local Development
```bash
# Terminal 1: Server
python mcp_http_server.py

# Terminal 2: GUI Client
python mcp_http_client_app.py http://localhost:8000 ./workspace

# Terminal 3: AI Host
python mcp_http_host_app.py http://localhost:8000 ./workspace
```

### Docker
```bash
docker build -t mcp-app .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY -p 8000:8000 -p 7862:7862 mcp-app
```

### GitHub Actions CI/CD
- ✅ Automated testing on Python 3.9-3.11
- ✅ Runs on Linux, macOS, Windows
- ✅ Code quality checks (pylint, black, flake8, mypy)
- ✅ Security checks (bandit, safety)
- ✅ Coverage reporting

See [PROJECT_REVIEW.md](PROJECT_REVIEW.md) for deployment details.

## 🛠️ Tools & Technologies

### Core
- **FastMCP** 2.12.5: MCP server framework
- **OpenAI SDK** 2.6.1: GPT model integration
- **Gradio** 5.49.1: Web UI framework
- **Uvicorn** 0.38.0: ASGI server
- **HTTPx**: HTTP client

### Testing
- **Pytest** 7.4.3: Test framework
- **Pytest-asyncio**: Async test support
- **Pytest-cov**: Coverage reporting
- **Black, Pylint, Flake8, MyPy**: Code quality

## 📝 API Reference

### Server Tools

```python
read_file(filepath: str) -> str
  # Read file from workspace

write_file(filepath: str, content: str) -> str
  # Write file to workspace

list_files(directory: str) -> List[str]
  # List directory contents

analyze_code(code: str, focus: str = "") -> str
  # Analyze code with LLM
```

### Client Methods

```python
await client.connect()
await client.list_tools()
await client.call_tool(name, arguments)
await client.list_resources()
await client.read_resource(uri)
await client.list_prompts()
await client.get_prompt(name, arguments)
```

## 🔐 Security Considerations

### ✅ Implemented
- Path traversal prevention
- Input validation on all parameters
- UTF-8 encoding enforcement
- Error message safety
- Dependency security checks (CI/CD)

### ⚠️ To Implement
- API authentication
- Authorization/RBAC
- Rate limiting
- Request signing
- Data encryption at rest

See [PROJECT_REVIEW.md](PROJECT_REVIEW.md#security-checklist) for security details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

All PRs must:
- ✅ Pass all tests
- ✅ Maintain 90%+ coverage
- ✅ Pass code quality checks
- ✅ Include documentation

## 📋 Project Status

### ✅ Completed
- HTTP MCP server with filesystem tools
- Gradio web UI for tool exploration
- OpenAI integration with function calling
- Configuration management system
- 75+ test cases with CI/CD pipeline
- Comprehensive documentation
- Security hardening
- Resilience patterns

### 🚧 In Progress
- Enhanced monitoring and metrics
- Performance optimization
- Extended logging

### 📋 Planned
- Multi-instance load balancing
- Persistent conversation storage
- Database-backed file storage
- Authentication/authorization
- WebSocket support
- Batch operations
- Custom tool templates

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 👥 Author

Deepak Upadhyay - Engineering

## 🙏 Acknowledgments

- FastMCP team for MCP server framework
- OpenAI for GPT model APIs
- Gradio for web UI components
- Python async/await ecosystem

## 📞 Support

For issues, questions, or feature requests:

1. **Check Documentation**
   - [QUICKSTART.md](QUICKSTART.md) - Common tasks
   - [CONFIG.md](CONFIG.md) - Configuration help
   - [TESTING.md](TESTING.md) - Test documentation

2. **Review Examples**
   - Check [tests/](tests/) for usage examples
   - Review [mcp_config.json](mcp_config.json) for setup

3. **Debug Issues**
   - Enable debug logging: `LOG_LEVEL=DEBUG`
   - Check [PROJECT_REVIEW.md](PROJECT_REVIEW.md) for architecture
   - Run tests: `pytest -v` to verify setup

## 🎓 Learning Resources

- [Model Context Protocol Spec](https://modelcontextprotocol.io/)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Gradio Documentation](https://gradio.app/)

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Status**: Production Ready ✅

Made with ❤️ for the agentic engineering community.

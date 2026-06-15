# Quick Start Guide

## 5-Minute Setup

### Prerequisites
- Python 3.9+
- pip package manager
- OpenAI API key

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Set Up Environment

Create `.env` file:
```bash
export OPENAI_API_KEY=sk-your-api-key-here
export OPENAI_MODEL=gpt-4o-mini
```

### Step 3: Start the Server

```bash
python mcp_http_server.py
```

Output:
```
Starting HTTP MCP Server on http://127.0.0.1:8000
Workspace root directory: /path/to/workspace
```

### Step 4: Start the GUI Client (Optional - new terminal)

```bash
python mcp_http_client_app.py http://127.0.0.1:8000 ./workspace
```

Access at: `http://127.0.0.1:7861`

### Step 5: Start the AI Host (Optional - new terminal)

```bash
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace
```

Access at: `http://127.0.0.1:7862`

---

## Configuration

### Quick Config

**Option 1: Environment Variables (Fastest)**
```bash
export OPENAI_API_KEY=sk-xxx
export OPENAI_MODEL=gpt-4o-mini
```

**Option 2: Config File**
```bash
cp mcp_config.example.json mcp_config.json
# Edit mcp_config.json with your settings
```

**Option 3: Command Line**
```bash
python mcp_http_host_app.py http://localhost:8000 ./workspace mcp_config.json gpt-4o sk-xxx
```

---

## Testing

### Run All Tests
```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

### Run Specific Tests
```bash
pytest tests/test_config.py -v                    # Config tests
pytest tests/test_server.py -v                    # Server tests
pytest tests/test_client_base.py -v               # Client tests
```

### With Coverage
```bash
pytest tests/ -v --cov=. --cov-report=html
open htmlcov/index.html
```

---

## Common Tasks

### Read a File
```bash
# Via GUI Client
1. Go to "Tools" tab
2. Click "List Tools"
3. Select "read_file"
4. Enter: {"filepath": "test.txt"}
5. Click "Call Tool"

# Via CLI (if using AI Host)
"Read the file test.txt from workspace"
```

### Write a File
```bash
# Via GUI Client
1. Go to "Tools" tab
2. Select "write_file"
3. Enter: {"filepath": "new.txt", "content": "Hello World"}
4. Click "Call Tool"
```

### List Files
```bash
# Via GUI Client
1. Go to "Tools" tab
2. Select "list_files"
3. Enter: {"directory": "."}
4. Click "Call Tool"
```

### Chat with AI
```bash
# Via AI Host App
1. Go to http://127.0.0.1:7862
2. Type: "List the files in workspace and read test.txt"
3. Press Enter

The AI will:
- Call list_files tool
- Call read_file tool
- Return the results
```

---

## Troubleshooting

### "Connection refused"
```bash
✓ Make sure server is running: python mcp_http_server.py
✓ Check the URL matches: http://127.0.0.1:8000
✓ Wait 2 seconds and try again (port may be in use)
```

### "API key not found"
```bash
✓ Set: export OPENAI_API_KEY=sk-xxx
✓ Or add to mcp_config.json: "api_key": "${OPENAI_API_KEY}"
✓ Check .env file is in project root
```

### "Model not found"
```bash
✓ Verify model name: gpt-4o-mini, gpt-4o, gpt-4, gpt-3.5-turbo
✓ Check your OpenAI account has access to the model
✓ Set: export OPENAI_MODEL=gpt-4o-mini
```

### "Access denied - path outside workspace"
```bash
✓ This is intentional security feature
✓ All file operations limited to workspace directory
✓ Put files in ./workspace/ directory
```

### "File not found"
```bash
✓ Create files first: touch workspace/test.txt
✓ Or write via write_file tool
✓ Check file path is relative to workspace/
```

---

## Project Structure

```
project/
├── mcp_http_server.py        # Start here: the server
├── mcp_http_client_app.py    # Optional: GUI interface
├── mcp_http_host_app.py      # Optional: AI agent
├── mcp_config.json           # Configuration
├── workspace/                # File storage
├── tests/                    # Test suite (75+ tests)
├── requirements.txt          # Dependencies
├── CONFIG.md                 # Detailed configuration
├── TESTING.md                # Testing guide
└── PROJECT_REVIEW.md         # Full review
```

---

## Next Steps

1. **Explore** - Check `workspace/README.md`
2. **Configure** - Edit `mcp_config.json` 
3. **Test** - Run `pytest tests/`
4. **Deploy** - See `PROJECT_REVIEW.md`
5. **Extend** - Add custom tools to `mcp_http_server.py`

---

## Key Commands Reference

| Task | Command |
|------|---------|
| Start server | `python mcp_http_server.py` |
| Start GUI | `python mcp_http_client_app.py http://127.0.0.1:8000 ./workspace` |
| Start AI Host | `python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace` |
| Run tests | `pytest tests/ -v` |
| Coverage report | `pytest --cov=. --cov-report=html` |
| Check config | `grep -r OPENAI_API_KEY` |
| View logs | Scroll terminal or add `--log-cli-level=DEBUG` |

---

## Documentation

- **Configuration**: See [CONFIG.md](CONFIG.md)
- **Testing**: See [TESTING.md](TESTING.md)
- **Full Review**: See [PROJECT_REVIEW.md](PROJECT_REVIEW.md)
- **Examples**: Check [tests/](tests/) for usage examples

---

## Performance Tips

1. **Keep workspace clean** - Fewer files = faster listing
2. **Use appropriate model** - gpt-4o-mini faster than gpt-4o
3. **Enable caching** - Reuse connections (auto-enabled)
4. **Monitor logs** - Set `LOG_LEVEL=INFO` in production
5. **Bound history** - Keep conversations focused (20 message limit)

---

## Support

- **Errors**: Check terminal logs and error messages
- **Config issues**: See CONFIG.md section on troubleshooting
- **Test failures**: See TESTING.md section on running tests
- **Performance**: Check PROJECT_REVIEW.md Performance section

---

Enjoy! 🚀

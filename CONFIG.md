# Configuration Guide for MCP HTTP Host App

## Overview

The MCP HTTP Host App supports flexible configuration through multiple methods:

1. **Configuration File** (mcp_config.json)
2. **Environment Variables** (.env)
3. **Command Line Arguments**
4. **Default Values**

## Configuration Priority

Configuration values are resolved in this order (highest to lowest priority):

```
1. Command Line Arguments    (most specific)
2. Configuration File (mcp_config.json)
3. Environment Variables (.env)
4. Default Values            (least specific)
```

This means you can override config file values with environment variables, and override everything with command line arguments.

---

## Configuration File (mcp_config.json)

Create `mcp_config.json` in the same directory as `mcp_http_host_app.py`:

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

### Key Features:

- **Environment Variable Substitution**: Use `${VAR_NAME}` syntax to reference environment variables
  - Example: `"api_key": "${OPENAI_API_KEY}"` will be replaced with the value of `$OPENAI_API_KEY`
- **Auto-Discovery**: If `mcp_config.json` exists in the script directory, it's automatically loaded
- **JSON Format**: Standard JSON format for easy parsing and validation

### Configuration Options:

| Section | Key | Type | Default | Description |
|---------|-----|------|---------|-------------|
| openai | api_key | string | (from env) | OpenAI API key |
| openai | model | string | gpt-4o-mini | OpenAI model to use |
| server | host | string | 127.0.0.1 | MCP server host |
| server | port | integer | 8000 | MCP server port |
| gui | host | string | 127.0.0.1 | GUI server host |
| gui | port | integer | 7862 | GUI server port |
| logging | level | string | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |

---

## Environment Variables

Create a `.env` file (or export variables) to configure the application:

```bash
# OpenAI Configuration
export OPENAI_API_KEY=sk-your-api-key-here
export OPENAI_MODEL=gpt-4o-mini

# GUI Configuration
export MCP_HOST_HOST=127.0.0.1
export MCP_HOST_PORT=7862

# Logging
export LOG_LEVEL=INFO
```

### Supported Variables:

| Variable | Default | Description |
|----------|---------|-------------|
| OPENAI_API_KEY | (required) | Your OpenAI API key |
| OPENAI_MODEL | gpt-4o-mini | Model name |
| MCP_HOST_HOST | 127.0.0.1 | GUI server address |
| MCP_HOST_PORT | 7862 | GUI server port |
| LOG_LEVEL | INFO | Logging level |

---

## Command Line Arguments

```bash
python mcp_http_host_app.py <server_url> <roots_dir> [config_file] [model] [api_key]
```

### Arguments:

| Argument | Required | Example | Description |
|----------|----------|---------|-------------|
| server_url | Yes | http://127.0.0.1:8000 | MCP server URL |
| roots_dir | Yes | /path/to/workspace | Workspace directory |
| config_file | No | mcp_config.json | Config file path |
| model | No | gpt-4o | Model override |
| api_key | No | sk-... | API key override |

### Examples:

```bash
# Use default config and environment
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace

# Use custom config file
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace custom_config.json

# Override model
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace mcp_config.json gpt-4o

# Override model and API key
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace mcp_config.json gpt-4o sk-xyz123
```

---

## Setup Examples

### Example 1: Using Config File + Environment Variables

**mcp_config.json:**
```json
{
  "openai": {
    "api_key": "${OPENAI_API_KEY}",
    "model": "gpt-4o"
  },
  "gui": {
    "port": 7862
  }
}
```

**.env:**
```bash
export OPENAI_API_KEY=sk-your-actual-key
```

**Run:**
```bash
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace
```

---

### Example 2: Using Only Environment Variables

**.env:**
```bash
export OPENAI_API_KEY=sk-your-actual-key
export OPENAI_MODEL=gpt-4o-turbo
export MCP_HOST_PORT=8000
```

**Run:**
```bash
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace
```

---

### Example 3: Using Command Line Overrides

**Run:**
```bash
python mcp_http_host_app.py http://127.0.0.1:8000 ./workspace mcp_config.json gpt-4o sk-temporary-key
```

---

## Configuration Output

On startup, the app will print a configuration summary:

```
============================================================
Configuration Summary
============================================================
Config File: /path/to/mcp_config.json
OpenAI Model: gpt-4o
OpenAI API Key: Configured ✓
Server: 127.0.0.1:8000
GUI: 127.0.0.1:7862
Log Level: INFO
============================================================
```

---

## Troubleshooting

### Config file not found
If `mcp_config.json` doesn't exist, the app will use environment variables and defaults:
```
WARNING: Config file not found: /path/to/mcp_config.json. Using environment variables and defaults.
```

### Environment variable substitution not working
Make sure the syntax is correct: `"${VAR_NAME}"`
- ✅ Correct: `"api_key": "${OPENAI_API_KEY}"`
- ❌ Wrong: `"api_key": "$OPENAI_API_KEY"`
- ❌ Wrong: `"api_key": "{OPENAI_API_KEY}"`

### API key is invalid error
Check these in order:
1. Command line argument (if provided)
2. Config file (`mcp_config.json`)
3. Environment variable (`OPENAI_API_KEY`)
4. OpenAI's default environment

### Wrong model being used
Check the priority:
1. Command line argument (3rd or 4th arg)
2. Config file `openai.model`
3. Environment variable `OPENAI_MODEL`
4. Default: `gpt-4o-mini`

---

## Best Practices

1. **Store secrets in .env, not in mcp_config.json**
   - Add `.env` to `.gitignore`
   - Share `mcp_config.example.json` instead

2. **Use config file for project defaults**
   - Keep stable settings in `mcp_config.json`
   - Use env vars for secrets and local overrides

3. **Use command line for temporary overrides**
   - Perfect for testing with different models

4. **Always verify config on startup**
   - Check the configuration summary printed when the app starts

---

## Files

| File | Purpose |
|------|---------|
| mcp_config.json | Active configuration (auto-loaded) |
| mcp_config.example.json | Template configuration (reference) |
| .env | Environment variables (git-ignored) |
| .env.example | Example environment variables |
| mcp_config.py | Configuration manager module |

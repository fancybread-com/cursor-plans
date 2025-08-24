# Setup Instructions for Cursor Plans MCP

## Prerequisites

**Important**: This MCP server requires Python 3.10 or later due to MCP library requirements.

### Check Your Python Version

```bash
python3 --version
# Should show Python 3.10.x or later
```

### If You Need Python 3.10+

#### Option 1: Using Homebrew (macOS)
```bash
brew install python@3.10
# or
brew install python@3.11
```

#### Option 2: Using pyenv
```bash
# Install pyenv if you don't have it
curl https://pyenv.run | bash

# Install Python 3.11
pyenv install 3.11.0
pyenv local 3.11.0
```

#### Option 3: Download from python.org
Visit https://www.python.org/downloads/ and download Python 3.10+ installer.

## Installation Steps

### 1. Clone and Setup Virtual Environment

```bash
cd /path/to/cursor-plans

# Create virtual environment with Python 3.10+
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip

# Install the project in development mode
pip install -e .
```

### 3. Test the Installation

```bash
# Test the server
python -m cursor_plans_mcp.server --help

# Should show:
# Usage: python -m cursor_plans_mcp.server [OPTIONS]
# Options:
#   --port INTEGER          Port to listen on for SSE
#   --transport [stdio|sse] Transport type
#   --help                  Show this message and exit.
```

### 4. Run a Quick Test

```bash
# Create a test plan
python3 -c "
import asyncio
from cursor_plans_mcp.server import create_dev_plan

async def test():
    result = await create_dev_plan({'name': 'test-project', 'template': 'basic'})
    print(result[0].text)

asyncio.run(test())
"
```

## Integration with Cursor

### 1. Configure MCP in Cursor

Add to your Cursor MCP configuration:

```json
{
  "mcpServers": {
    "cursor-plans": {
      "command": "/path/to/your/.venv/bin/python",
      "args": ["-m", "cursor_plans_mcp.server", "--transport", "stdio"]
    }
  }
}
```

### 2. Available Tools

Once configured, you'll have access to these tools in Cursor:

- `dev_plan_create` - Create new development plans
- `dev_plan_show` - Display existing plans
- `dev_state_show` - Analyze current codebase state
- `dev_state_diff` - Compare current vs target state

## Troubleshooting

### "ModuleNotFoundError: No module named 'cursor_plans_mcp'"

Make sure your virtual environment is activated and the package is installed:
```bash
source .venv/bin/activate
pip install -e .
```

### "ModuleNotFoundError: No module named 'mcp'"

The MCP library requires Python 3.10+. Check your Python version:
```bash
python3 --version
```

### MCP Server Not Showing in Cursor

1. Check the path in your MCP configuration
2. Ensure the virtual environment is properly set up
3. Test the server manually: `python -m cursor_plans_mcp.server --help`

## Next Steps

1. Create your first development plan: `dev_plan_create name="my-project"`
2. Analyze your current codebase: `dev_state_show`
3. Compare states: `dev_state_diff`
4. Explore the generated `.devplan` files

## Development

To contribute or modify the server:

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests (when available)
pytest

# Format code
ruff format .

# Type check
pyright
```

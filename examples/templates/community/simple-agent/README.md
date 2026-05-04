# Simple Weather Agent

A minimal agent template for the Oh My Coder community, demonstrating how to build a single-file agent with tool integration.

## Features

- 🌤️ **Weather Query**: Fetches real-time weather data via wttr.in (no API key needed for weather)
- 🛠️ **Tool System**: Uses `@tool` decorator from omc core
- 🤖 **LLM Integration**: OpenAI-compatible API support
- 📝 **Type Hints**: Full type annotation with Pydantic models
- 🧪 **Test Ready**: pytest configuration included

## Quick Start

### 1. Install Dependencies

```bash
# Using pip
pip install -e ".[dev]"

# Using uv (recommended)
uv pip install -e ".[dev]"
```

### 2. Set API Key

```bash
export OPENAI_API_KEY="your-api-key-here"
```

### 3. Run the Agent

```bash
python weather_agent.py
```

Example interaction:
```
🌤️  Simple Weather Agent
========================================
Type 'quit' to exit

You: What's the weather in Tokyo?
Agent: 🌤️ Tokyo: Partly cloudy, +22°C, humidity 65%

Powered by Oh My Coder Community Template

You: quit
Goodbye! 👋
```

## Project Structure

```
simple-agent/
├── weather_agent.py    # Main agent implementation
├── pyproject.toml      # Dependencies and tool config
├── README.md           # This file
└── tests/              # Test directory (create yourself)
    └── test_weather.py
```

## Development

### Run Tests

```bash
pytest
```

### Code Quality

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Type checking
mypy weather_agent.py
```

## Customization Guide

### Add a New Tool

```python
from src.core.tool import tool

@tool(description="Your tool description")
def my_tool(param: str) -> str:
    """Tool implementation."""
    return f"Result: {param}"
```

Then register it in the agent:
```python
self.register_tool(my_tool)
```

### Change LLM Provider

Modify the `LLMClient` initialization:
```python
self.llm = LLMClient(
    api_key=self.api_key,
    base_url="https://api.deepseek.com/v1",  # Your provider
    model="deepseek-chat"
)
```

## License

MIT - See Oh My Coder main repository for details.

## Contributing

This is a community template. Improvements welcome!
See [CONTRIBUTING.md](../../../CONTRIBUTING.md) for guidelines.

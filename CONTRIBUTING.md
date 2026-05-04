# Contributing to Oh My Coder

Thank you for your interest in contributing! This guide will help you get started quickly.

## Quick Start

### 1. Fork & Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/oh-my-coder.git
cd oh-my-coder

# Add upstream remote
git remote add upstream https://github.com/VOBC/oh-my-coder.git
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"

# Verify installation
omc --version
```

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_agent.py -v
```

## Development Workflow

### Branch Naming

```
feature/your-feature-name    # New features
fix/bug-description          # Bug fixes
docs/improvement             # Documentation
refactor/component           # Code refactoring
test/add-coverage            # Tests only
```

### Making Changes

```bash
# Create a new branch
git checkout -b feature/my-feature

# Make your changes, then run quality checks
ruff check src/ tests/          # Linting
ruff format src/ tests/         # Formatting
pytest                          # Tests

# Commit with conventional format (see below)
git add .
git commit -m "feat: add new feature"

# Push to your fork
git push origin feature/my-feature

# Create Pull Request on GitHub
```

## Code Standards

### Python Style

We use **ruff** for linting and formatting:

```bash
# Auto-fix issues
ruff check --fix src/ tests/

# Format code
ruff format src/ tests/
```

Rules enforced:
- Line length: 88 characters
- Import sorting (I001)
- Type annotations required for public APIs
- Docstrings: Google style

### Type Hints

All public functions must have type annotations:

```python
def process_data(data: dict[str, Any]) -> Result:
    """Process input data and return result.
    
    Args:
        data: Input dictionary to process
        
    Returns:
        Processed result object
        
    Raises:
        ValueError: If data format is invalid
    """
    ...
```

### Testing

- Write tests for all new features
- Maintain >80% code coverage
- Use pytest fixtures for shared setup
- Mock external API calls

Example:
```python
def test_feature():
    """Test description."""
    input_data = {"key": "value"}
    result = process(input_data)
    assert result.status == "success"
```

## Commit Message Format

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Code style (formatting, no logic change) |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvement |
| `ci` | CI/CD changes |

### Examples

```bash
feat(agent): add streaming response support
fix(tools): handle timeout in weather API
docs(readme): update installation instructions
refactor(core): simplify tool registration
test(agent): add edge case coverage for chat
```

### Scope Guidelines

Common scopes:
- `agent` - Agent core functionality
- `tools` - Tool system
- `cli` - Command line interface
- `config` - Configuration management
- `docs` - Documentation
- `tests` - Test suite
- `deps` - Dependencies

## Pull Request Process

1. **Before Submitting**
   - [ ] All tests pass locally
   - [ ] Code is formatted with ruff
   - [ ] New features have tests
   - [ ] Documentation updated if needed
   - [ ] Commit messages follow convention

2. **PR Description**
   - Clear title with type prefix
   - Description of changes
   - Link to related issue (if applicable)
   - Screenshots for UI changes

3. **Review Process**
   - Maintainers will review within 48 hours
   - Address review comments with additional commits
   - Squash commits if requested

## Community Templates

Want to contribute a template? See `examples/templates/community/` for examples.

Template requirements:
- Working code example
- README with usage instructions
- pyproject.toml with dependencies
- Basic tests

## Getting Help

- 💬 Discussions: [GitHub Discussions](https://github.com/VOBC/oh-my-coder/discussions)
- 🐛 Issues: [GitHub Issues](https://github.com/VOBC/oh-my-coder/issues)
- 📧 Email: vobc@example.com (for sensitive matters)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

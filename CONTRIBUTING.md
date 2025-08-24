# Contributing to Cursor Plans

Thank you for your interest in contributing to Cursor Plans! This document provides guidelines and information for contributors.

## Development Setup

### Prerequisites

- Python 3.10 or later
- Git
- A code editor (Cursor recommended!)

### Local Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/your-username/cursor-plans.git
   cd cursor-plans
   ```

2. **Set up the development environment**
   ```bash
   # Create virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate

   # Install in development mode
   pip install -e .

   # Install development dependencies
   pip install -e ".[dev]"
   ```

3. **Verify the setup**
   ```bash
   python -m cursor_plans_mcp.server --help
   ```

## Project Structure

```
cursor-plans/
├── src/
│   └── cursor_plans_mcp/     # Main package
│       ├── __init__.py
│       ├── server.py         # MCP server entry point
│       ├── dsl/              # DSL parser and interpreter
│       ├── execution/        # Plan execution engine
│       ├── validation/       # Validation framework
│       ├── state/            # State management
│       └── templates/        # Code generation templates
├── tests/                    # Test suite
├── docs/                     # Documentation (future)
├── pyproject.toml           # Project configuration
└── README.md                # Project overview
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/cursor_plans_mcp

# Run specific test file
pytest tests/test_server.py
```

### 4. Code Quality Checks

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
pyright
```

### 5. Commit Your Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

### 6. Push and Create a Pull Request

```bash
git push origin feature/your-feature-name
```

## Code Style Guidelines

### Python Code

- Follow [PEP 8](https://peps.python.org/pep-0008/) style guidelines
- Use type hints for all function parameters and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused

### Commit Messages

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for formatting changes
- `refactor:` for code refactoring
- `test:` for adding or updating tests
- `chore:` for maintenance tasks

### Example Commit Messages

```bash
feat: add support for custom validation rules
fix: resolve issue with plan execution on Windows
docs: update installation instructions for Python 3.13
test: add comprehensive tests for DSL parser
```

## Testing Guidelines

### Writing Tests

- Write tests for all new functionality
- Use descriptive test names
- Test both success and failure cases
- Mock external dependencies

### Test Structure

```python
def test_feature_name():
    """Test description of what is being tested."""
    # Arrange
    input_data = {...}

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result.expected_value == "expected"
```

## Documentation

### Code Documentation

- Use docstrings for all public APIs
- Follow Google or NumPy docstring format
- Include examples in docstrings

### User Documentation

- Update README.md for user-facing changes
- Update SETUP.md for installation changes
- Add inline comments for complex logic

## Pull Request Guidelines

### Before Submitting

1. **Ensure tests pass**
   ```bash
   pytest
   ```

2. **Run code quality checks**
   ```bash
   ruff format .
   ruff check .
   pyright
   ```

3. **Update documentation**
   - Update README.md if needed
   - Add inline comments for complex code
   - Update docstrings

4. **Test your changes**
   - Test the MCP server locally
   - Verify integration with Cursor
   - Test with different Python versions

### Pull Request Template

When creating a pull request, include:

- **Description**: What does this PR do?
- **Type of change**: Bug fix, feature, documentation, etc.
- **Testing**: How was this tested?
- **Breaking changes**: Any breaking changes?
- **Related issues**: Link to related issues

## Getting Help

- **Issues**: Use GitHub issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Code Review**: All PRs require review before merging

## Release Process

1. **Version bump**: Update version in `pyproject.toml`
2. **Changelog**: Update CHANGELOG.md
3. **Tag release**: Create a git tag
4. **Publish**: Release to PyPI (when ready)

## License

By contributing to Cursor Plans, you agree that your contributions will be licensed under the MIT License.

Thank you for contributing! 🚀

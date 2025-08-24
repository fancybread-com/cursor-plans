# GitHub Actions Workflows

This directory contains GitHub Actions workflows for the Cursor Plans project.

## Workflows

### CI (`ci.yml`)
Runs on every push and pull request to `main` and `develop` branches.

**Jobs:**
- **Test**: Runs core tests across Python 3.10, 3.11, and 3.12
- **Lint**: Runs ruff linting and mypy type checking
- **Build**: Builds the Python package (wheel and sdist)
- **Security**: Runs bandit security checks

### Release (`release.yml`)
Runs when a tag starting with `v` is pushed (e.g., `v1.0.0`).

**Actions:**
- Builds the package
- Publishes to PyPI (requires `PYPI_API_TOKEN` secret)
- Creates a GitHub release

### Security (`security.yml`)
Runs weekly and can be triggered manually.

**Actions:**
- Runs bandit security checks
- Runs safety dependency vulnerability checks
- Comments on PRs if vulnerabilities are found

## Dependabot Configuration

The `dependabot.yml` file configures automated dependency updates:

- **Python dependencies**: Weekly updates on Mondays
- **GitHub Actions**: Weekly updates on Mondays
- **Development dependencies**: Separate updates for dev tools

## Secrets Required

For full functionality, set up these repository secrets:

- `PYPI_API_TOKEN`: PyPI API token for publishing packages

## Local Testing

To test workflows locally:

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/test_mcp_tools.py tests/test_name_resolution.py tests/test_init_tool.py tests/test_schema_documentation.py tests/test_dotnet_templates.py

# Run linting
ruff check src/ tests/
ruff format --check src/ tests/

# Run type checking
mypy src/cursor_plans_mcp/

# Build package
python -m build

# Run security checks
bandit -r src/cursor_plans_mcp/
```

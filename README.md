# Cursor Plans

A Terraform-like Domain Specific Language (DSL) for structured software development planning with Cursor.

## Overview

Cursor Plans MCP brings Infrastructure-as-Code principles to application development, providing explicit control over codebase state transitions through declarative planning, validation, and atomic execution.

## Features

- **Declarative Development Plans**: Define your target codebase state in `.devplan` files
- **State Tracking**: Compare current vs desired state
- **Multi-Layer Validation**: Syntax, logic, context, and team standards validation
- **Cursor Rules Integration**: Validate against `.cursorrules` coding standards
- **Template System**: Reusable code generation patterns
- **Context Management**: Story-specific file context for better planning

## Installation

> **📋 For detailed setup instructions, see [SETUP.md](SETUP.md)**

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -e .
   ```

## Usage

### 0. Initialize Development Planning (Recommended)

```bash
# Initialize development planning for your project:
plan_init project_directory="/path/to/your/project"

# Start over (purge all plans and reset context):
plan_init project_directory="/path/to/your/project" reset=true
```

This tool:
- Creates the `.cursorplans/` directory in your project
- Detects your project type (Python, Node.js, .NET, etc.)
- Provides the exact `project_directory` path for future commands
- Shows recommended templates for your project type
- **Reset mode**: Purges all `.devplan` files, context files, and resets project context

### 1. Initialize Development Planning

```bash
# Initialize development planning for your project:
plan_init context="project-context.yaml" project_directory="/path/to/your/project"
```

This sets up the `.cursorplans/` directory and loads your project context.

### 2. Prepare a Development Plan

```bash
# Create a development plan from templates:
plan_prepare name="my-project" template="fastapi"
```

This creates a `my-project.devplan` file with structured development goals in your project directory.

### 3. Validate the Plan

```bash
# Validate plan quality and compliance
plan_validate plan_file="my-project.devplan"
```

### 4. Execute Plans

```bash
# Dry run - see what would be executed
plan_apply plan_file="my-project.devplan" dry_run=true

# Execute the plan
plan_apply plan_file="my-project.devplan"
```

### 5. Manage State

```bash
# List available snapshots
# Note: Snapshot management tools are currently being refactored
# For now, use the core planning tools above
```



## Important Parameters

### project_directory

**Note**: The `project_directory` parameter is automatically handled by the `plan_init` tool. After initialization, you don't need to specify it in every command.

```bash
# ✅ New 4-phase workflow
plan_init context="project-context.yaml" project_directory="/Users/paul/projects/my-project"
plan_prepare name="my-project" template="basic"
```

**Why this matters**: The `plan_init` tool stores the project context, so files are always created in your project's local `.cursorplans/` directory instead of the global location.

### Reset/Start Over

When you need to completely start over with development planning:

```bash
# Purge all plans and reset context
plan_init project_directory="/path/to/your/project" reset=true
```

This will:
- Remove all `.devplan` files
- Remove all context files (`context*.txt`)
- Remove any JSON configuration files
- Reset the stored project context
- Create a fresh `.cursorplans/` directory

**Use cases**:
- Starting a new feature branch
- Changing project direction
- Cleaning up experimental plans
- Resolving corrupted state

## Development Plan Structure

```yaml
# project.devplan
project:
  name: "my-service"
  version: "1.0.0"

target_state:
  architecture:
    - language: "python"
    - framework: "FastAPI"
    - database: "PostgreSQL"

resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "fastapi_main"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_project_structure
      - install_dependencies
```

## Available Templates

### ✅ Fully Implemented Templates
- **basic**: Simple project structure with generic templates
- **fastapi**: FastAPI web service with database, authentication, and OpenAPI docs
- **dotnet**: .NET 8 Web API with Entity Framework, JWT authentication, and Swagger
- **vuejs**: Vue.js frontend application with routing and state management
- **from-existing**: Analyze existing codebase and create plan

### 📋 Template Implementation Status
- **✅ 9 templates fully implemented** (generate actual code)
- **⚠️ 11 templates referenced** (fall back to basic template)
- **🔧 Custom templates** supported with `custom_` prefix

For detailed template information, see [SCHEMA.md](SCHEMA.md#template-names).

## Available Tools

### Core Planning Tools
- **`plan_init`** - Initialize development planning and load project context
- **`plan_prepare`** - Create development plans from templates
- **`plan_validate`** - Validate plan syntax, logic, and compliance
- **`plan_apply`** - Execute development plans to create/modify files

For detailed usage examples, see [HOW-TO.md](HOW-TO.md).

## Integration with Cursor

This MCP server integrates seamlessly with Cursor, providing:

- Interactive development planning
- Real-time state analysis
- Template-based code generation
- Structured workflow management

## Roadmap

### ✅ Completed Features
- [x] 4-phase development workflow (`plan_init`, `plan_prepare`, `plan_validate`, `plan_apply`) ✅
- [x] Validation framework ✅
- [x] Template system with 9 fully implemented templates ✅
- [x] .NET template support ✅
- [x] Context-aware project directory handling ✅
- [x] Template implementation status tracking ✅

### 🚧 In Progress
- [ ] Advanced template implementations (Vue.js, additional Python templates)
- [ ] Enhanced validation rules
- [ ] Better error handling and user feedback

### 🔮 Future Features
- [ ] Git integration
- [ ] Parallel execution
- [ ] Custom task definitions
- [ ] Template marketplace
- [ ] CI/CD integration

## Contributing

This is an experimental project exploring Infrastructure-as-Code principles for software development. Contributions and feedback are welcome!

### Development Setup

1. Clone the repository
2. Install dependencies: `pip install -e ".[dev]"`
3. Run tests: `pytest tests/`
4. Run linting: `ruff check src/ tests/`

### CI/CD

The project uses GitHub Actions for continuous integration:

- **CI**: Runs tests, linting, and builds on every PR
- **Release**: Automatically publishes to PyPI when tags are pushed
- **Security**: Weekly security scans and vulnerability checks
- **Dependabot**: Automated dependency updates

See [`.github/README.md`](.github/README.md) for detailed workflow information.

## License

MIT
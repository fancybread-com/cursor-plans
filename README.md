# Cursor Plans

A Terraform-like Domain Specific Language (DSL) for structured software development planning with Cursor.

## Overview

Cursor Plans MCP brings Infrastructure-as-Code principles to application development, providing explicit control over codebase state transitions through declarative planning, validation, and atomic execution.

## Features

- **Declarative Development Plans**: Define your target codebase state in `.devplan` files
- **State Tracking**: Compare current vs desired state
- **Multi-Layer Validation**: Syntax, logic, context, and team standards validation
- **Cursor Rules Integration**: Validate against `.cursorrules` coding standards
- **Template System**: Reusable code generation patterns for multiple languages
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

## Supported Languages & Templates

### 🐍 **Python**

#### **FastAPI Templates** ✅ Fully Implemented
- **`fastapi_main`** - FastAPI application entry point with basic endpoints
- **`fastapi_model`** - Pydantic model definitions with configuration
- **`requirements`** - Python dependencies file with FastAPI ecosystem

#### **Basic Templates** ✅ Fully Implemented
- **`basic`** - Generic template fallback for any file type
- **`stub`** - Stub/placeholder template for creating directory structure

### ⚡ **TypeScript/JavaScript**

#### **Vue.js Templates** ⚠️ Referenced (Fallback to basic)
- **`vue_main`** - Vue.js main application entry point
- **`vue_app`** - Vue.js app component
- **`vue_router`** - Vue Router configuration
- **`pinia_store`** - Pinia state management store
- **`vue_component`** - Vue component template
- **`vue_package_json`** - Package.json with Vue dependencies

#### **Node.js Templates** ⚠️ Referenced (Fallback to basic)
- **`node_main`** - Node.js application entry point
- **`express_app`** - Express.js application setup
- **`nextjs_app`** - Next.js application configuration

### ☕ **Java**

#### **Spring Templates** ⚠️ Referenced (Fallback to basic)
- **`spring_main`** - Spring Boot main application class
- **`spring_controller`** - Spring REST controller
- **`spring_service`** - Spring service layer
- **`spring_repository`** - Spring Data repository

#### **Build System Templates** ⚠️ Referenced (Fallback to basic)
- **`maven_pom`** - Maven POM configuration
- **`gradle_build`** - Gradle build configuration

### 🔷 **C# (.NET)**

#### **.NET Templates** ✅ Fully Implemented
- **`dotnet_program`** - .NET 8 Web API Program.cs with Swagger
- **`dotnet_controller`** - ASP.NET Core API controller
- **`ef_dbcontext`** - Entity Framework DbContext
- **`dotnet_service`** - .NET service layer with authentication
- **`dotnet_csproj`** - .NET project file configuration

## Template Implementation Status

### ✅ **Fully Implemented (10 templates)**
- **Python**: `fastapi_main`, `fastapi_model`, `requirements`
- **Generic**: `basic`, `stub`
- **.NET**: `dotnet_program`, `dotnet_controller`, `ef_dbcontext`, `dotnet_service`, `dotnet_csproj`

### ⚠️ **Referenced Templates (11 templates)**
- **Python**: `python_main`, `sqlalchemy_models`, `jwt_auth`
- **TypeScript**: `vue_main`, `vue_app`, `vue_router`, `pinia_store`, `vue_component`, `vue_package_json`
- **Java**: `spring_main`, `spring_controller`, `spring_service`, `maven_pom`, `gradle_build`
- **Generic**: `basic_readme`

**Note**: Referenced templates fall back to the `basic` template and generate placeholder content.

### 🔧 **Custom Templates**
- Unlimited custom templates with `custom_` prefix
- Must be implemented in the execution engine

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
- [x] Template system with 10 fully implemented templates ✅
- [x] .NET template support ✅
- [x] Python FastAPI template support ✅
- [x] Context-aware project directory handling ✅
- [x] Template implementation status tracking ✅

### 🚧 In Progress
- [ ] Advanced template implementations (Vue.js, Spring Boot, additional Python templates)
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
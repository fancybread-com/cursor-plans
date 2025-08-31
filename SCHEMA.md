# Development Plan Schema Documentation

## Overview

Development plans use a strict YAML schema with versioning to ensure consistency and prevent validation errors. All plan files must conform to this schema.

## Schema Version

Current schema version: `1.0`

## Required Fields

### Project Metadata
```yaml
project:
  name: "project-name"          # Required: Project name
  version: "1.0.0"             # Required: Project version
  description: "Description"    # Required: Project description
```

### Target State
```yaml
target_state:
  architecture:                 # Required: Architecture components
    - language: "python"        # Optional: Programming language
    - framework: "FastAPI"      # Optional: Framework
    - type: "Web API"          # Optional: Project type
  features:                     # Required: Target features
    - "api_endpoints"
    - "authentication"
```

### Resources
```yaml
resources:
  files:                        # Required: Files to create
    - path: "src/main.py"       # Required: File path
      type: "entry_point"       # Required: File type
      template: "fastapi_main"  # Required: Template name
  dependencies:                 # Required: Package dependencies (strings only)
    - "fastapi"
    - "sqlalchemy"
```

### Phases
```yaml
phases:                         # Required: Development phases
  foundation:                   # Phase name
    priority: 1                 # Required: Priority number
    description: "Setup"        # Optional: Phase description
    dependencies: []            # Optional: Phase dependencies
    tasks:                      # Required: Phase tasks
      - "setup_project"
  testing:                      # Required: Must include testing phase
    priority: 5
    tasks:
      - "unit_tests"
```

### Validation
```yaml
validation:                     # Required: Validation rules
  pre_apply:                    # Required: Pre-apply validations
    - "syntax_check"
  post_apply:                   # Optional: Post-apply validations
    - "unit_test_validation"
```

### Constraints (Optional)
```yaml
constraints:                    # Optional: Project constraints
  - name: "performance"
    description: "Must be fast"
```

## Template Names

### ✅ Supported Templates (Fully Implemented)
These templates are implemented in the execution engine and will generate actual file content:

#### Python/FastAPI Templates
- `fastapi_main` - FastAPI main application with basic endpoints
- `fastapi_model` - Pydantic model template with BaseModel
- `requirements` - Python requirements.txt with FastAPI dependencies

#### .NET Templates
- `dotnet_program` - .NET Program.cs with Web API setup
- `dotnet_controller` - ASP.NET Core controller template
- `ef_dbcontext` - Entity Framework DbContext
- `dotnet_service` - .NET service layer with authentication
- `dotnet_csproj` - .NET project file with dependencies

#### Generic Templates
- `basic` - Generic template fallback for any file type
- `stub` - Stub/placeholder template for creating directory structure and basic files

### ⚠️ Referenced Templates (Not Yet Implemented)
These templates are referenced in plan generation but **not yet implemented** in the execution engine. They will fall back to the `basic` template:

**Note**: .NET templates (`dotnet_program`, `dotnet_controller`, `ef_dbcontext`, `dotnet_service`, `dotnet_csproj`) are now **fully implemented** and moved to the Supported Templates section above.

#### Python/FastAPI Templates
- `basic_readme` - Project README template
- `python_main` - Python main application
- `sqlalchemy_models` - SQLAlchemy model definitions
- `jwt_auth` - JWT authentication setup
- `fastapi_requirements` - FastAPI-specific requirements

#### Vue.js Templates
- `vue_main` - Vue.js main application
- `vue_app` - Vue.js App.vue component
- `vue_router` - Vue Router configuration
- `pinia_store` - Pinia state management
- `vue_component` - Vue.js component template
- `vue_package_json` - Vue.js package.json

### 🔧 Custom Templates
Use `custom_` prefix for custom templates:
```yaml
template: "custom_my_template"
```

**Note**: Custom templates are not validated by the schema but should be implemented in the execution engine to generate actual content.

### 📁 Stub Template Usage
The `stub` template is specifically designed for creating placeholder files and directory structure:

```yaml
resources:
  files:
    - path: "src/my_module/__init__.py"
      type: "component_init"
      template: "stub"  # Creates basic __init__.py file
    - path: "templates/my_template"
      type: "template_file"
      template: "stub"  # Creates template directory and basic file
```

**Use cases**:
- Component initialization files (`__init__.py`)
- Template directory structures
- Placeholder files for future implementation
- Scaffolding for complex project structures

### Template Implementation Status
- **✅ Implemented**: 10 templates (fastapi_main, fastapi_model, requirements, basic, stub, dotnet_program, dotnet_controller, ef_dbcontext, dotnet_service, dotnet_csproj)
- **⚠️ Referenced**: 11 templates (fall back to basic template)
- **🔧 Custom**: Unlimited (with custom_ prefix)

**Future Work**: The referenced templates are planned for implementation in future releases. Currently, they will generate placeholder content using the `basic` template.

### Validation Behavior
- **Schema validation**: Allows both implemented and referenced templates
- **Execution behavior**:
  - Implemented templates generate actual content
  - Referenced templates fall back to `basic` template (placeholder content)
  - `stub` template creates directory structure and basic placeholder files
  - Custom templates must be implemented in the execution engine

## Validation Rules

1. **Schema Version**: Must be present and valid
2. **Required Phases**: Must include `testing` phase
3. **Dependencies Format**: Must be strings, not objects
4. **Template Names**: Must be standard or use `custom_` prefix
5. **File Paths**: Must be valid relative paths

## Example Valid Plan

```yaml
schema_version: "1.0"
project:
  name: "my-api"
  version: "1.0.0"
  description: "REST API service"

target_state:
  architecture:
    - language: "python"
    - framework: "FastAPI"
  features:
    - "api_endpoints"
    - "authentication"

resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "fastapi_main"
  dependencies:
    - "fastapi"
    - "sqlalchemy"

phases:
  foundation:
    priority: 1
    tasks:
      - "setup_project"
  testing:
    priority: 2
    tasks:
      - "unit_tests"

validation:
  pre_apply:
    - "syntax_check"
  post_apply:
    - "unit_test_validation"
```

## Error Messages

Common validation errors and solutions:

- **"Missing required phases: ['testing']"**: Add a testing phase
- **"Unknown template 'xyz'"**: Use `custom_xyz` or choose from standard templates
- **"Input should be a valid string"**: Dependencies must be strings, not objects
- **"Schema validation error"**: Check all required fields are present

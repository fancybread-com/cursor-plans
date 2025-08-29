"""Cursor Plans MCP Server - Development Planning DSL for Cursor."""

from typing import Any
import json
import os
from pathlib import Path

import anyio
import click
import mcp.types as types
from mcp.server.lowlevel import Server

from .validation import ValidationEngine
from .execution import PlanExecutor
from .schema import validate_plan_content, create_validated_plan_content

# Global state to store project context
_project_context: dict[str, Any] = {}


@click.command()
@click.option("--port", default=8000, help="Port to listen on for SSE")
@click.option(
    "--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)
def main(port: int, transport: str) -> int:
    """Main entry point for the Cursor Plans MCP server."""
    app = Server("cursor-plans-mcp")

    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """List all available development planning tools."""
        return [
            types.Tool(
                name="plan_init",
                title="Initialize Development Planning",
                description="Initialize development planning",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "context": {
                            "type": "string",
                            "description": "Path to YAML context file containing project configuration and file patterns",
                        },
                        "project_directory": {
                            "type": "string",
                            "description": "Project directory (default: current working directory)",
                            "default": ".",
                        },
                        "reset": {
                            "type": "boolean",
                            "description": "Reset/start over: purge all .devplan files and reset context",
                            "default": False,
                        },
                    },
                    "required": ["context"],
                },
            ),
            types.Tool(
                name="plan_prepare",
                title="Prepare Development Plan",
                description="Create a development plan from templates",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "Name of the development plan to create",
                            "default": "project",
                        },
                        "template": {
                            "type": "string",
                            "description": "Template to use (basic, fastapi, dotnet, vuejs)",
                            "default": "basic",
                        },
                    },
                    "required": [],
                },
            ),




            types.Tool(
                name="plan_validate",
                title="Validate Development Plan",
                description="Validate development plan syntax, logic, and compliance",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_file": {
                            "type": "string",
                            "description": "Path to .devplan file (default: ./.cursorplans/project.devplan)",
                            "default": "./project.devplan",
                        },
                        "strict_mode": {
                            "type": "boolean",
                            "description": "If true, warnings are treated as errors",
                            "default": False,
                        },
                        "check_cursor_rules": {
                            "type": "boolean",
                            "description": "If true, validate against .cursorrules file",
                            "default": True,
                        },
                    },
                },
            ),
            types.Tool(
                name="plan_apply",
                title="Apply Development Plan",
                description="Execute a development plan to create/modify files",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "plan_file": {
                            "type": "string",
                            "description": "Path to .devplan file (default: ./.cursorplans/project.devplan)",
                            "default": "./project.devplan",
                        },
                        "dry_run": {
                            "type": "boolean",
                            "description": "Show what would be executed without making changes",
                            "default": False,
                        },
                    },
                },
            ),


        ]

    @app.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        """Handle tool calls for development planning operations."""

        if name == "plan_init":
            return await init_dev_planning(arguments)
        elif name == "plan_prepare":
            return await prepare_dev_plan(arguments)
        elif name == "plan_validate":
            return await validate_dev_plan(arguments)
        elif name == "plan_apply":
            return await apply_dev_plan(arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")

    # Transport setup
    if transport == "sse":
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.requests import Request
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        sse = SseServerTransport("/messages/")

        async def handle_sse(request: Request):
            async with sse.connect_sse(request.scope, request.receive, request._send) as streams:  # type: ignore[reportPrivateUsage]
                await app.run(streams[0], streams[1], app.create_initialization_options())
            return Response()

        starlette_app = Starlette(
            debug=True,
            routes=[
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        import uvicorn

        uvicorn.run(starlette_app, host="127.0.0.1", port=port)
    else:
        from mcp.server.stdio import stdio_server

        async def arun():
            async with stdio_server() as streams:
                await app.run(streams[0], streams[1], app.create_initialization_options())

        anyio.run(arun)

    return 0


async def prepare_dev_plan(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Create a development plan using stored context information."""
    global _project_context

    name = arguments.get("name", "project")
    template = arguments.get("template", "basic")

    # Use stored project context if available
    if not _project_context:
        return [
            types.TextContent(
                type="text",
                text="❌ **Error**: No project context found. Please run plan_init first.\n\nUsage: plan_init context=\"project-context.yaml\""
            )
        ]

    project_path = Path(_project_context.get("project_directory", "."))
    cursorplans_dir = project_path / ".cursorplans"

    # Ensure .cursorplans directory exists
    if not cursorplans_dir.exists():
        cursorplans_dir.mkdir(exist_ok=True)

    # Create the development plan
    plan_creation_result = await _create_plan_file(
        name, template, project_path, cursorplans_dir,
        _project_context.get("project_name", name),
        _project_context.get("project_type", "unknown"),
        _project_context.get("project_description", "A software project"),
        _project_context.get("objectives", []),
        _project_context.get("architecture_notes", []),
        _project_context.get("context_files", [])
    )

    # Generate success message
    if plan_creation_result["success"]:
        success_message = f"""✅ **Development Plan Created**

📄 **Plan File**: `{plan_creation_result['plan_file']}`
🎯 **Name**: `{name}`
🔧 **Template**: `{template}`

**Next Steps:**
1. Validate your plan:
   ```bash
   plan_validate plan_file="{name}.devplan"
   ```

2. Apply your plan:
   ```bash
   plan_apply plan_file="{name}.devplan" dry_run=true
   ```
"""
    else:
        success_message = f"❌ **Plan Creation Failed**\n\n{plan_creation_result['error']}"

    return [
        types.TextContent(
            type="text",
            text=success_message
        )
    ]


async def init_dev_planning(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Initialize development planning."""
    import os
    import shutil
    from pathlib import Path
    import yaml
    global _project_context

    context_file = arguments.get("context")
    project_directory = arguments.get("project_directory", ".")
    reset = arguments.get("reset", False)

    if not context_file:
        return [
            types.TextContent(
                type="text",
                text="❌ **Error**: Context file path is required.\n\nUsage: dev_plan_init context=\"sample.context.yaml\""
            )
        ]

    # Load and parse the context file
    try:
        context_path = Path(context_file)
        if not context_path.exists():
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ **Error**: Context file not found: {context_file}"
                )
            ]

        with open(context_path, 'r') as f:
            context_config = yaml.safe_load(f)

        if not context_config or 'project' not in context_config:
            return [
                types.TextContent(
                    type="text",
                    text=f"❌ **Error**: Invalid context file format. Missing 'project' section in {context_file}"
                )
            ]

    except yaml.YAMLError as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Error**: Invalid YAML in context file: {str(e)}"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Error**: Could not read context file: {str(e)}"
            )
        ]

    # Extract project configuration
    project_config = context_config['project']
    # Use parameter project_directory if provided, otherwise use context file directory
    if arguments.get("project_directory") and arguments.get("project_directory") != ".":
        project_directory = arguments.get("project_directory")
    else:
        project_directory = project_config.get('directory', '.')
    project_name = project_config.get('name', 'unknown')
    project_type = project_config.get('type', 'unknown')
    project_description = project_config.get('description', '')
    project_objectives = project_config.get('objectives', [])
    architecture_notes = project_config.get('architecture_notes', [])

    # Resolve the project directory
    if project_directory == "." or not project_directory:
        project_directory = os.getcwd()

    project_path = Path(project_directory).resolve()

    # Handle reset functionality
    if reset:
        cursorplans_dir = project_path / ".cursorplans"
        context_files = []

        # Collect all files to be removed
        if cursorplans_dir.exists():
            for file in cursorplans_dir.glob("*.devplan"):
                context_files.append(str(file))
            for file in cursorplans_dir.glob("*.yaml"):
                context_files.append(str(file))

        # Remove .cursorplans directory and all contents
        if cursorplans_dir.exists():
            shutil.rmtree(cursorplans_dir)

        # Reset global context
        _project_context = {}

        # Create fresh .cursorplans directory
        cursorplans_dir.mkdir(exist_ok=True)

        reset_output = f"""🔄 **Development Planning Reset Complete**

📁 **Project Directory**: `{project_path}`
🗑️ **Purged Files**: {len(context_files)} files
📂 **Fresh Plans Directory**: `{cursorplans_dir}`

✅ **Ready to start over!**

**Next Steps:**
1. Create a new context file and run init again:
   ```bash
   dev_plan_init context="my-project.context.yaml"
   ```
"""
        return [
            types.TextContent(
                type="text",
                text=reset_output
            )
        ]

    # Scan for context files based on the YAML configuration
    context_files = context_config.get('context_files', {})
    scanned_files = []

    # Process each category of context files
    for category, patterns in context_files.items():
        for pattern in patterns:
            try:
                # Handle glob patterns
                if pattern.endswith('/'):
                    # For directory patterns, search recursively for files
                    matches = list(project_path.glob(pattern + "**/*"))
                else:
                    matches = list(project_path.glob(pattern))

                for match in matches:
                    if match.is_file():
                        rel_path = str(match.relative_to(project_path))
                        scanned_files.append(f"{category}: {rel_path}")
            except Exception:
                # Skip invalid patterns
                continue

    # Store enhanced project context in global state
    _project_context = {
        "project_directory": str(project_path),
        "project_name": project_name,
        "project_type": project_type,
        "project_description": project_description,
        "objectives": project_objectives,
        "architecture_notes": architecture_notes,
        "context_files": scanned_files,
        "cursorplans_dir": str(project_path / ".cursorplans"),
        "context_config_path": str(context_path.resolve())
    }

    # Create .cursorplans directory
    cursorplans_dir = project_path / ".cursorplans"
    try:
        cursorplans_dir.mkdir(exist_ok=True)
    except FileNotFoundError:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Error**: Project directory does not exist: {project_directory}"
            )
        ]

    # Generate comprehensive initialization output
    objectives_text = ""
    if project_objectives:
        objectives_text = f"""
🎯 **Project Objectives**:
{chr(10).join(f"  • {obj}" for obj in project_objectives)}"""

    architecture_text = ""
    if architecture_notes:
        architecture_text = f"""
🏗️ **Architecture Notes**:
{chr(10).join(f"  • {note}" for note in architecture_notes)}"""

    context_text = ""
    if scanned_files:
        context_text = f"""
📁 **Context Files Found**: {len(scanned_files)} files
{chr(10).join(f"  • {f}" for f in scanned_files[:10])}
{"  • ..." if len(scanned_files) > 10 else ""}"""

    init_output = f"""🚀 **Development Planning Initialized**

📁 **Project Directory**: `{project_path}`
🏷️ **Project Name**: `{project_name}`
🔧 **Project Type**: `{project_type}`
📋 **Description**: {project_description}
📂 **Plans Directory**: `{cursorplans_dir}`
🔗 **Context File**: `{context_file}`{objectives_text}{architecture_text}{context_text}

✅ **Ready to create development plans!**

**Next Steps:**
1. Create your first plan:
   ```bash
   plan_prepare name="my-project" template="basic"
   ```

2. Validate your plan:
   ```bash
   plan_validate plan_file="my-project.devplan"
   ```

3. Apply your plan:
   ```bash
   plan_apply plan_file="my-project.devplan" dry_run=true
   ```
"""

    return [
        types.TextContent(
            type="text",
            text=init_output
        )
    ]


async def _create_plan_file(name: str, template: str, project_path: Path, cursorplans_dir: Path,
                           project_name: str, project_type: str, project_description: str,
                           objectives: list, architecture_notes: list, context_files: list) -> dict:
    """Helper function to create a plan file."""
    try:
        # Generate plan content using the same logic as create_dev_plan
        def generate_base_plan(name, project_type, project_description):
            """Pass 1: Generate base plan structure"""
            return f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: "{project_description}"

target_state:
  architecture:
    - language: "{project_type}"
    - project_type: "{project_type}"

  features:
    - basic_structure
    - documentation

resources:
  files:
    - path: "README.md"
      type: "documentation"
      template: "basic_readme"

  dependencies:
    - "requests"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_project_structure
      - create_basic_files

  development:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - implement_core_features
      - add_tests

  testing:
    priority: 3
    dependencies: ["development"]
    tasks:
      - unit_tests
      - integration_tests

validation:
  pre_apply:
    - syntax_check

  post_apply:
    - functionality_test
"""

        def apply_context_to_plan(base_plan, objectives, architecture_notes, context_files):
            """Pass 2: Apply context to enhance the plan"""
            enhanced_plan = base_plan

            # Add objectives section if we have objectives
            if objectives:
                objectives_yaml = "\n".join(f'    - "{obj}"' for obj in objectives)
                objectives_section = f"""
  objectives:
{objectives_yaml}"""
                enhanced_plan = enhanced_plan.replace(
                    f'  description: "{project_description}"',
                    f'  description: "{project_description}"{objectives_section}'
                )

            # Add architecture constraints if we have them
            if architecture_notes:
                arch_yaml = "\n".join(f'    - "{note}"' for note in architecture_notes)
                architecture_section = f"""
  architecture_constraints:
{arch_yaml}"""
                enhanced_plan = enhanced_plan.replace(
                    objectives_section if objectives else f'  description: "{project_description}"',
                    (objectives_section if objectives else f'  description: "{project_description}"') + architecture_section
                )

            return enhanced_plan

        # Generate plan content
        base_plan = generate_base_plan(name, project_type, project_description)
        plan_content = apply_context_to_plan(base_plan, objectives, architecture_notes, context_files)

        # Add template-specific content
        if template == "fastapi":
            plan_content = _get_fastapi_template(name)
        elif template == "dotnet":
            plan_content = _get_dotnet_template(name)
        elif template == "vuejs":
            plan_content = _get_vuejs_template(name)

        # Validate plan content
        from .schema import validate_plan_content
        is_valid, error_msg, _ = validate_plan_content(plan_content)
        if not is_valid:
            return {"success": False, "error": f"Schema validation failed: {error_msg}"}

        # Write the plan file
        plan_file = cursorplans_dir / f"{name}.devplan"
        with open(plan_file, "w") as f:
            f.write(plan_content)

        return {"success": True, "plan_file": str(plan_file)}

    except Exception as e:
        return {"success": False, "error": str(e)}


def _get_fastapi_template(name: str) -> str:
    """Get FastAPI template content."""
    return f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: "FastAPI web service with database"

target_state:
  architecture:
    - language: "Python"
    - framework: "FastAPI"
    - database: "SQLAlchemy"
    - auth: "JWT"

  features:
    - api_endpoints
    - database_models
    - authentication
    - documentation
    - testing

resources:
  files:
    - path: "src/main.py"
      type: "entry_point"
      template: "fastapi_main"
    - path: "src/models.py"
      type: "data_model"
      template: "fastapi_model"
    - path: "requirements.txt"
      type: "dependencies"
      template: "requirements"

  dependencies:
    - "fastapi>=0.104.0"
    - "uvicorn>=0.24.0"
    - "sqlalchemy>=2.0.0"
    - "pyjwt>=2.8.0"
    - "python-multipart>=0.0.6"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_project_structure
      - install_dependencies

  data_layer:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - create_models
      - setup_database

  api_layer:
    priority: 3
    dependencies: ["data_layer"]
    tasks:
      - create_endpoints
      - add_validation

  security:
    priority: 4
    dependencies: ["api_layer"]
    tasks:
      - implement_jwt
      - add_auth_middleware

  testing:
    priority: 5
    dependencies: ["security"]
    tasks:
      - unit_tests
      - integration_tests

validation:
  pre_apply:
    - syntax_check
    - dependency_check

  post_apply:
    - api_test_validation
"""


def _get_dotnet_template(name: str) -> str:
    """Get .NET template content."""
    return f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: ".NET 8 Web API with Entity Framework"

target_state:
  architecture:
    - language: "C#"
    - framework: ".NET 8"
    - type: "Web API"
    - database: "Entity Framework Core"
    - auth: "JWT Bearer"

  features:
    - web_api
    - entity_framework
    - jwt_authentication
    - swagger_documentation
    - unit_testing

resources:
  files:
    - path: "Program.cs"
      type: "entry_point"
      template: "dotnet_program"
    - path: "Controllers/BaseController.cs"
      type: "api_controller"
      template: "dotnet_controller"
    - path: "Data/AppDbContext.cs"
      type: "data_context"
      template: "ef_dbcontext"
    - path: "Services/AuthService.cs"
      type: "service_interface"
      template: "dotnet_service"
    - path: "{name}.csproj"
      type: "project_file"
      template: "dotnet_csproj"

  dependencies:
    - name: "Microsoft.AspNetCore.Authentication.JwtBearer"
      version: "8.0.0"
    - name: "Microsoft.EntityFrameworkCore.SqlServer"
      version: "8.0.0"
    - name: "Swashbuckle.AspNetCore"
      version: "6.5.0"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_project_structure
      - install_dependencies

  data_layer:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - create_models
      - setup_entity_framework

  api_layer:
    priority: 3
    dependencies: ["data_layer"]
    tasks:
      - create_endpoints
      - add_controllers

  security:
    priority: 4
    dependencies: ["api_layer"]
    tasks:
      - implement_jwt
      - add_auth_middleware

  testing:
    priority: 5
    dependencies: ["security"]
    tasks:
      - unit_tests
      - integration_tests

validation:
  pre_apply:
    - syntax_check
    - dependency_check

  post_apply:
    - build_test
"""


def _get_vuejs_template(name: str) -> str:
    """Get Vue.js template content."""
    return f"""schema_version: "1.0"
# Development Plan: {name}

project:
  name: "{name}"
  version: "0.1.0"
  description: "Vue.js frontend application"

target_state:
  architecture:
    - language: "TypeScript"
    - framework: "Vue 3"
    - build_tool: "Vite"
    - state_management: "Pinia"
    - ui_framework: "Vuetify"
    - testing: "Vitest + Vue Test Utils"

  features:
    - component_library
    - routing
    - state_management
    - api_integration
    - responsive_design
    - unit_testing

resources:
  files:
    - path: "src/main.ts"
      type: "entry_point"
      template: "vue_main"
    - path: "src/App.vue"
      type: "root_component"
      template: "vue_app"
    - path: "src/router/index.ts"
      type: "router_config"
      template: "vue_router"
    - path: "src/stores/main.ts"
      type: "state_store"
      template: "pinia_store"
    - path: "src/components/HelloWorld.vue"
      type: "component"
      template: "vue_component"
    - path: "package.json"
      type: "dependencies"
      template: "vue_package_json"

  dependencies:
    - name: "vue"
      version: "^3.4.0"
    - name: "vue-router"
      version: "^4.2.0"
    - name: "pinia"
      version: "^2.1.0"
    - name: "vuetify"
      version: "^3.5.0"
    - name: "axios"
      version: "^1.6.0"

phases:
  foundation:
    priority: 1
    tasks:
      - setup_vite_project
      - configure_typescript
      - setup_vuetify

  routing:
    priority: 2
    dependencies: ["foundation"]
    tasks:
      - configure_vue_router
      - create_route_components
      - implement_navigation

  state_management:
    priority: 3
    dependencies: ["routing"]
    tasks:
      - setup_pinia_stores
      - implement_state_logic
      - connect_components_to_store

  components:
    priority: 4
    dependencies: ["state_management"]
    tasks:
      - create_reusable_components
      - implement_forms
      - add_data_tables

  api_integration:
    priority: 5
    dependencies: ["components"]
    tasks:
      - setup_axios_client
      - implement_api_services
      - handle_authentication

  testing:
    priority: 6
    dependencies: ["api_integration"]
    tasks:
      - unit_tests
      - component_tests
      - e2e_tests

validation:
  pre_apply:
    - typescript_check
    - vue_template_validation
    - dependency_audit
"""







async def load_context_file(context_file_path: str) -> list[str]:
    """Load context files from a text file."""
    context_files = []
    try:
        with open(context_file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    context_files.append(line)
    except FileNotFoundError:
        pass
    return context_files




async def detect_existing_codebase(directory: str, context_files: list[str] = None, suggest_name: bool = True) -> dict[str, Any]:
    """Detect the framework and structure of an existing codebase."""
    current_dir = Path(directory)
    detected_info = {
        "framework": None,
        "language": None,
        "suggested_name": None,
        "key_files": [],
        "structure": "unknown"
    }

    # If suggest_name is False, we won't set any suggested_name
    if not suggest_name:
        detected_info["suggested_name"] = None

    try:
        # If context files are provided, focus on those first
        if context_files:
            context_paths = []
            for context_file in context_files:
                context_path = current_dir / context_file
                if context_path.exists():
                    if context_path.is_file():
                        context_paths.append(context_path)
                    else:
                        # If it's a directory, add all files in it (limited scope)
                        try:
                            for item in context_path.rglob("*"):
                                if item.is_file():
                                    context_paths.append(item)
                        except (PermissionError, OSError):
                            pass
            files = context_paths
        else:
            # Check for various framework indicators (limited scope)
            files = []
            # Get immediate files only
            for item in current_dir.iterdir():
                if item.is_file():
                    files.append(item)

            # Only scan specific known project directories
            project_dirs = ["cursor-plans", "src", "tests", "docs", "examples"]
            for dir_name in project_dirs:
                project_dir = current_dir / dir_name
                if project_dir.exists() and project_dir.is_dir():
                    try:
                        for item in project_dir.rglob("*"):
                            if item.is_file():
                                files.append(item)
                    except (PermissionError, OSError):
                        pass

        file_names = [f.name for f in files if f.is_file()]

        # .NET detection
        if any(f.endswith('.csproj') or f.endswith('.sln') for f in file_names):
            detected_info["framework"] = "dotnet"
            detected_info["language"] = "C#"
            detected_info["structure"] = "dotnet_project"

            # Try to get project name from .csproj
            if suggest_name:
                for f in files:
                    if f.name.endswith('.csproj'):
                        detected_info["suggested_name"] = f.stem
                        break
            else:
                # Ensure suggested_name stays None when suggest_name is False
                detected_info["suggested_name"] = None

        # Vue.js detection
        elif "package.json" in file_names:
            try:
                package_json_path = current_dir / "package.json"
                if package_json_path.exists():
                    with open(package_json_path, 'r') as f:
                        package_data = json.loads(f.read())
                        deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}

                        if 'vue' in deps:
                            detected_info["framework"] = "vuejs"
                            detected_info["language"] = "JavaScript/TypeScript"
                            detected_info["structure"] = "vue_project"
                            if suggest_name:
                                detected_info["suggested_name"] = package_data.get("name", "vue-app")
                            else:
                                detected_info["suggested_name"] = None
                        elif 'react' in deps:
                            detected_info["framework"] = "react"
                            detected_info["language"] = "JavaScript/TypeScript"
                            detected_info["structure"] = "react_project"
                            if suggest_name:
                                detected_info["suggested_name"] = package_data.get("name", "react-app")
                            else:
                                detected_info["suggested_name"] = None
            except (json.JSONDecodeError, FileNotFoundError):
                pass

        # Python/FastAPI detection
        elif any(f in file_names for f in ["requirements.txt", "pyproject.toml", "setup.py"]):
            detected_info["framework"] = "fastapi"
            detected_info["language"] = "Python"
            detected_info["structure"] = "python_project"

            # Check if it's specifically FastAPI
            try:
                if "requirements.txt" in file_names:
                    with open(current_dir / "requirements.txt", 'r') as f:
                        reqs = f.read().lower()
                        if 'fastapi' in reqs:
                            detected_info["framework"] = "fastapi"
                        elif 'django' in reqs:
                            detected_info["framework"] = "django"
                        elif 'flask' in reqs:
                            detected_info["framework"] = "flask"
            except FileNotFoundError:
                pass

        # Collect key files for context
        key_patterns = [
            "*.csproj", "*.sln", "Program.cs", "Startup.cs",  # .NET
            "package.json", "vite.config.*", "vue.config.*", "src/main.*",  # Vue/JS
            "requirements.txt", "pyproject.toml", "main.py", "app.py",  # Python
            "README.*", "LICENSE", ".gitignore", "Dockerfile"  # Common
        ]

        for pattern in key_patterns:
            matches = list(current_dir.glob(pattern))
            detected_info["key_files"].extend([str(f.relative_to(current_dir)) for f in matches])

    except Exception as e:
        print(f"Error detecting codebase: {e}")

    return detected_info









async def validate_dev_plan(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Validate development plan syntax, logic, and compliance."""
    plan_file = arguments.get("plan_file", "./project.devplan")
    strict_mode = arguments.get("strict_mode", False)
    check_cursor_rules = arguments.get("check_cursor_rules", True)

    try:
        # If no specific path is provided, look in .cursorplans directory first
        if plan_file == "./project.devplan":
            cursorplans_path = Path(".cursorplans") / "project.devplan"
            if cursorplans_path.exists():
                plan_file = str(cursorplans_path)

        # Initialize validation engine
        validation_engine = ValidationEngine()

        # Run validation
        result = await validation_engine.validate_plan_file(
            plan_file_path=plan_file,
            strict_mode=strict_mode,
            check_cursor_rules=check_cursor_rules
        )

        # Format results for Cursor chat
        formatted_result = result.format_for_cursor()

        return [
            types.TextContent(
                type="text",
                text=formatted_result
            )
        ]

    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ Validation engine error: {str(e)}\n\nThis may indicate a configuration issue with the validation system."
            )
        ]


async def apply_dev_plan(arguments: dict[str, Any]) -> list[types.ContentBlock]:
    """Execute a development plan to create/modify files."""
    plan_file = arguments.get("plan_file", "./project.devplan")
    dry_run = arguments.get("dry_run", False)

    try:
        # If no specific path is provided, look in .cursorplans directory first
        if plan_file == "./project.devplan":
            cursorplans_path = Path(".cursorplans") / "project.devplan"
            if cursorplans_path.exists():
                plan_file = str(cursorplans_path)

        # Initialize execution engine
        executor = PlanExecutor()

        # Execute the plan
        result = await executor.execute_plan(plan_file, dry_run=dry_run)

        # Format results for Cursor chat
        if result.success:
            if dry_run:
                output = f"🔍 **Dry Run Results**\n\n"
                output += f"✅ Would execute {len(result.executed_phases)} phases:\n"
                for phase in result.executed_phases:
                    output += f"  - {phase}\n"

                if result.changes_made:
                    output += f"\n📝 **Would create/modify:**\n"
                    for change in result.changes_made:
                        output += f"  - {change}\n"
            else:
                output = f"✅ **Plan Execution Completed**\n\n"
                output += f"🎯 **Executed {len(result.executed_phases)} phases:**\n"
                for phase in result.executed_phases:
                    output += f"  - {phase}\n"

                if result.changes_made:
                    output += f"\n📝 **Changes made:**\n"
                    for change in result.changes_made:
                        output += f"  - {change}\n"

                if result.snapshot_id:
                    output += f"\n💾 **Snapshot created:** {result.snapshot_id}\n"

                if result.execution_time:
                    output += f"⏱️ **Execution time:** {result.execution_time:.2f}s\n"
        else:
            output = f"❌ **Plan Execution Failed**\n\n"
            output += f"🚫 **Error:** {result.error_message}\n"

            if result.failed_phase:
                output += f"📋 **Failed at phase:** {result.failed_phase}\n"

            if result.executed_phases:
                output += f"✅ **Completed phases:** {', '.join(result.executed_phases)}\n"

            if result.snapshot_id:
                output += f"🔄 **Rollback attempted to:** {result.snapshot_id}\n"

        return [
            types.TextContent(
                type="text",
                text=output
            )
        ]

    except PermissionError as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Permission Error:** {str(e)}\n\n**Troubleshooting:**\n"
                     f"• Check if you have write permissions in the current directory\n"
                     f"• Try running Cursor with elevated permissions if needed\n"
                     f"• Ensure the target directory is not read-only\n"
                     f"• Check if any files are locked by other processes"
            )
        ]
    except OSError as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **OS Error:** {str(e)}\n\n**Troubleshooting:**\n"
                     f"• Check disk space and file system permissions\n"
                     f"• Ensure the target path is valid and accessible\n"
                     f"• Try creating the directory manually first"
            )
        ]
    except Exception as e:
        return [
            types.TextContent(
                type="text",
                text=f"❌ **Execution error:** {str(e)}\n\nThis may indicate a configuration issue with the execution system."
            )
        ]





if __name__ == "__main__":
    main()
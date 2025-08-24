# How to Use Cursor Plans MCP

## **Quick Reference - Most Common Commands**

```bash
# Initialize development planning for your project
dev_plan_init project_directory="/path/to/your/project"

# Create a new development plan
dev_plan_create name="my-project" template="fastapi"

# Show current project state
dev_state_show

# Compare current state with plan
dev_state_diff

# Validate a plan
dev_plan_validate

# Show available snapshots
dev_snapshots
```

## **Getting Started**

### 1. Initialize Development Planning

**First step for any project:**

```bash
# Initialize development planning for your project:
dev_plan_init project_directory="/path/to/your/project"

# Start over (purge all plans and reset context):
dev_plan_init project_directory="/path/to/your/project" reset=true
```

**What this does:**
- ✅ Creates the `.cursorplans/` directory in your project
- ✅ Detects your project type (Python, Node.js, .NET, etc.)
- ✅ Stores project context for future commands
- ✅ Shows recommended templates for your project type
- ✅ **Reset mode**: Purges all `.devplan` files and resets context

### 2. Create Your First Plan

```bash
# Create a development plan (project directory is remembered from init)
dev_plan_create name="my-api" template="fastapi"
```

**Available Templates:**
- `basic` - Simple project structure
- `fastapi` - FastAPI web service with database
- `dotnet` - .NET 8 Web API with Entity Framework
- `vuejs` - Vue.js frontend application

## **File Organization Best Practices**

Development plans are automatically stored in a `.cursorplans/` directory in your project root:

```
your-project/
├── .cursorplans/
│   ├── my-api.devplan
│   ├── feature-auth.devplan
│   └── api-v2.devplan
├── src/
├── README.md
└── ...
```

**Benefits:**
- ✅ Keeps plan files organized and separate from source code
- ✅ Prevents plan files from cluttering your project root
- ✅ Makes it easy to find and manage multiple plans
- ✅ Follows the convention of dot-prefixed configuration directories

## **Template Types Explained**

### **Available Templates**

| Template | Description | Best For | Status |
|----------|-------------|----------|---------|
| `basic` | Simple project structure | Learning, simple projects | ✅ Implemented |
| `fastapi` | FastAPI web service with auth | Python APIs, microservices | ✅ Implemented |
| `dotnet` | .NET 8 Web API with Entity Framework | C# applications, enterprise | ✅ Implemented |
| `vuejs` | Vue.js frontend with Vite | Frontend applications, SPAs | ⚠️ Referenced |

### **Template Features**

**FastAPI Template:**
- 5 phases: Foundation → Data Layer → API Layer → Security → Testing
- Includes: SQLAlchemy models, JWT auth, OpenAPI docs
- Dependencies: FastAPI, SQLAlchemy, PyJWT
- **Status**: ✅ Fully implemented with 3 templates

**DotNET Template:**
- 5 phases: Foundation → Data Layer → API Layer → Security → Testing
- Includes: Entity Framework, JWT Bearer auth, Swagger
- Dependencies: ASP.NET Core, EF Core, JWT Bearer
- **Status**: ✅ Fully implemented with 5 templates

**Vue.js Template:**
- 6 phases: Foundation → Routing → State → Components → API → Testing
- Includes: Vue Router, Pinia, Vuetify, Axios
- Dependencies: Vue 3, TypeScript, Vite
- **Status**: ⚠️ Referenced (fall back to basic template)

## **Direct Tool Call Examples**

Here are all the available tool calls you can directly use in Cursor's chat:

### **1. Initialize Development Planning**
```bash
dev_plan_init project_directory="/Users/paul/projects/my-project"
dev_plan_init project_directory="/Users/paul/projects/my-project" reset=true
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `project_directory` | string | ❌ No | Current directory | Path to your project directory |
| `reset` | boolean | ❌ No | `false` | Purge all plans and reset context |

### **2. Create Development Plans**
```bash
dev_plan_create name="my-api-project" template="fastapi"
dev_plan_create name="web-app" template="vuejs"
dev_plan_create name="backend-service" template="dotnet"
dev_plan_create name="simple-project" template="basic"
dev_plan_create name="existing-project" template="basic"
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `name` | string | ✅ Yes | - | Name of the development plan (creates `{name}.devplan`) |
| `template` | string | ❌ No | `basic` | Template to use: `basic`, `fastapi`, `dotnet`, `vuejs` |
| `context` | string | ❌ No | `""` | Context identifier (story-123, feature-auth, etc.) - creates `context-{name}.txt` |

**Advanced Examples:**
```bash
# Create plan with specific context
dev_plan_create name="auth-feature" template="fastapi" context="story-456"

# Create plan for existing project with context files
dev_plan_create name="api-v2" template="dotnet" context="feature-api"
```

### **3. Show and Display Plans**
```bash
dev_plan_show plan_file="my-api-project.devplan"
dev_plan_show plan_file=".cursorplans/project.devplan"
dev_plan_show
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plan_file` | string | ❌ No | `./project.devplan` | Path to .devplan file (looks in `.cursorplans/` first) |

### **4. Analyze Current State**
```bash
dev_state_show directory="."
dev_state_show directory="./src"
dev_state_show directory="/path/to/project"
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `directory` | string | ❌ No | `.` | Directory to analyze (current directory) |

### **5. Compare States**
```bash
dev_state_diff plan_file="my-api-project.devplan"
dev_state_diff plan_file=".cursorplans/project.devplan"
dev_state_diff
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plan_file` | string | ❌ No | `./project.devplan` | Path to .devplan file (looks in `.cursorplans/` first) |

### **6. Validate Plans**
```bash
dev_plan_validate plan_file="my-api-project.devplan"
dev_plan_validate plan_file="my-api-project.devplan" strict_mode=true
dev_plan_validate plan_file="my-api-project.devplan" check_cursor_rules=false
dev_plan_validate
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plan_file` | string | ❌ No | `./project.devplan` | Path to .devplan file (looks in `.cursorplans/` first) |
| `strict_mode` | boolean | ❌ No | `false` | If true, warnings are treated as errors |
| `check_cursor_rules` | boolean | ❌ No | `true` | If true, validate against `.cursorrules` file |

### **7. Execute Plans**
```bash
dev_apply_plan plan_file="my-api-project.devplan" dry_run=true
dev_apply_plan plan_file="my-api-project.devplan"
dev_apply_plan
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `plan_file` | string | ❌ No | `./project.devplan` | Path to .devplan file (looks in `.cursorplans/` first) |
| `dry_run` | boolean | ❌ No | `false` | Show what would be executed without making changes |

### **8. Manage Snapshots**
```bash
dev_snapshots
dev_rollback snapshot_id="snapshot-20250823-123456-abc123"
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `snapshot_id` | string | ✅ Yes | - | ID of the snapshot to rollback to |

### **9. Context Management**
```bash
dev_context_list directory="."
dev_context_add files=["src/models.py", "controllers/"] context="story-123"
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `files` | array | ✅ Yes | - | List of files/directories to add to context |
| `context` | string | ❌ No | `main` | Context identifier (creates `context-{name}.txt`) |
| `description` | string | ❌ No | `""` | Optional description of the context |

## **Key Benefits**

1. **Structured Development** - Plans guide implementation order
2. **Consistency** - All code follows the planned architecture
3. **Progress Tracking** - See what's built vs what's planned
4. **Team Alignment** - Shared understanding of project structure
5. **Context Awareness** - Project directory is remembered across commands
6. **Template Implementation** - 9 templates fully implemented with actual code generation

## **Best Practices**

### **1. Start with Initialization**
Always begin new projects by initializing development planning:
```bash
dev_plan_init project_directory="/path/to/your/project"
```

### **2. Working with Existing Codebases**
For existing projects, manually specify relevant files to create accurate development plans:

#### **Method 1: Default Context**
Create a `context.txt` file in your project root with relevant file paths:
```
# context.txt
src/main.py
src/models.py
requirements.txt
README.md
```

Then create a plan:
```bash
dev_plan_create name="my-api" template="fastapi"
# Automatically uses context.txt if available
```

#### **Method 2: Story-Specific Context**
Add specific files to context for targeted planning:
```bash
# Add authentication files to context
dev_context_add files["src/auth.py", "src/models.py"] context="story-123"

# Create plan using that context
dev_plan_create name="auth-feature" template="fastapi" context="story-123"
```

#### **Method 3: Analyze Current State**
Use the state analysis tools to understand your codebase:
```bash
# Show current project structure
dev_state_show

# List files with context
dev_context_list include_content=true
```

### **3. Check State Regularly**
Monitor your progress against the plan:
```bash
dev_state_diff plan_file="my-project.devplan"
```

### **4. Use Natural Language**
Don't worry about exact tool names - just describe what you want:
```
"I want to see how my current code compares to my development plan"
```

### **5. Reference Plans in Context**
Use `@project.devplan` to give Cursor context about your intended structure.

### **6. Iterate and Refine**
Update your plans as requirements change - they're living documents.

### **7. Use Reset When Needed**
When starting over or changing direction:
```bash
dev_plan_init project_directory="/path/to/your/project" reset=true
```

## **Template Implementation Status**

### ✅ Fully Implemented (4 templates)
- **Basic**: `basic` - Simple project structure
- **FastAPI**: `fastapi` - Python FastAPI web service
- **.NET**: `dotnet` - .NET 8 Web API
- **Vue.js**: `vuejs` - Vue.js frontend application

### ⚠️ Referenced (6 templates)
- **Python/FastAPI**: `basic_readme`, `python_main`, `sqlalchemy_models`, `jwt_auth`, `fastapi_requirements`
- **Vue.js**: `vue_main`, `vue_app`, `vue_router`, `pinia_store`, `vue_component`, `vue_package_json`

**Note**: Referenced templates fall back to the `basic` template and generate placeholder content.

## **Troubleshooting**

### **Tools Not Showing**
- Restart Cursor completely
- Check MCP configuration in settings
- Verify green circle (connected) status

### **Plan Files Not Found**
- Development plans are stored in `.cursorplans/` directory by default
- Ensure `.devplan` files are in your project directory or `.cursorplans/` folder
- Use absolute paths if needed
- Check file permissions

### **State Analysis Issues**
- Run from your project root directory
- Ensure you have read permissions
- Check for hidden files that might be ignored

### **Project Directory Issues**
- Use `dev_plan_init` to set up project context
- The `project_directory` parameter is automatically remembered after initialization
- Use `reset=true` to clear context and start over

The tools work seamlessly in Cursor's chat - you just talk naturally about your development needs, and Cursor uses the planning tools behind the scenes to provide structured, consistent guidance!

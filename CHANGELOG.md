# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial release of Cursor Plans MCP server
- Terraform-like DSL for development planning
- Declarative development plan creation and execution
- Multi-layer validation framework
- State tracking and comparison
- Template system for code generation
- Context management for story-specific planning
- Integration with Cursor IDE via MCP protocol

### Features
- `plan_init` - Initialize development planning and load project context
- `plan_prepare` - Create development plans from templates
- `plan_validate` - Validate plan syntax, logic, and compliance
- `plan_apply` - Execute development plans (with dry-run support)
- 4-phase development workflow (init → prepare → validate → apply)
- Template system with 9 fully implemented templates
- Context-aware project directory handling

### Technical
- Modern Python project structure with src layout
- Python 3.10+ compatibility
- MCP (Model Context Protocol) server implementation
- Comprehensive test suite
- Type hints throughout codebase
- Ruff for linting and formatting
- Pyright for type checking

## [0.1.0] - 2024-08-24

### Added
- Initial alpha release
- Basic MCP server functionality
- Core DSL parsing and execution
- Template system with basic templates
- State management and snapshots
- Validation framework

### Templates Available
- `basic` - Simple project structure
- `fastapi` - FastAPI web service with database
- `dotnet` - .NET Core API with Entity Framework
- `vuejs` - Vue.js frontend application
- `from-existing` - Analyze existing codebase and create plan

---

## Version History

- **0.1.0** - Initial alpha release with core functionality
- **Unreleased** - Development version with latest features



---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

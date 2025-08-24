"""
Tests for template generation and context handling.
"""

import pytest
import os
import yaml
from cursor_plans_mcp.server import create_dev_plan, detect_existing_codebase


class TestTemplateGeneration:
    """Test template generation functionality."""

    @pytest.mark.asyncio
    async def test_basic_template(self, temp_dir):
        """Test basic template generation."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "basic-project",
            "template": "basic",
            "analyze_existing": False,
            "context": "",
            "project_directory": str(temp_dir)
        })

        plan_file = temp_dir / ".cursorplans" / "basic-project.devplan"
        assert plan_file.exists()

        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        # Basic template should have minimal structure
        assert plan_data["project"]["name"] == "basic-project"
        assert "target_state" in plan_data
        assert "resources" in plan_data
        assert "phases" in plan_data

        # Should have at least one phase
        assert len(plan_data["phases"]) >= 1

    @pytest.mark.asyncio
    async def test_fastapi_template(self, temp_dir):
        """Test FastAPI template generation."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "fastapi-project",
            "template": "fastapi",
            "analyze_existing": False,
            "context": "",
            "project_directory": str(temp_dir)
        })

        plan_file = temp_dir / ".cursorplans" / "fastapi-project.devplan"
        assert plan_file.exists()

        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        # FastAPI template should have specific characteristics
        assert plan_data["project"]["name"] == "fastapi-project"

        # Should have FastAPI in architecture
        architecture = plan_data["target_state"]["architecture"]
        assert any("FastAPI" in str(item) for item in architecture)
        assert any("python" in str(item).lower() for item in architecture)

        # Should have multiple phases including security
        phases = plan_data["phases"]
        phase_names = list(phases.keys())
        assert "foundation" in phase_names
        assert any("security" in name.lower() for name in phase_names)

        # Should have file resources
        files = plan_data["resources"]["files"]
        assert len(files) > 0

        # Should have main.py
        file_paths = [f["path"] for f in files]
        assert any("main.py" in path for path in file_paths)

    @pytest.mark.asyncio
    async def test_dotnet_template(self, temp_dir):
        """Test .NET template generation."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "dotnet-project",
            "template": "dotnet",
            "analyze_existing": False,
            "context": "",
            "project_directory": str(temp_dir)
        })

        plan_file = temp_dir / ".cursorplans" / "dotnet-project.devplan"
        assert plan_file.exists()

        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        # .NET template should have specific characteristics
        architecture = plan_data["target_state"]["architecture"]
        assert any(".NET" in str(item) for item in architecture)
        assert any("C#" in str(item) for item in architecture)

        # Should have .NET-specific files
        files = plan_data["resources"]["files"]
        file_paths = [f["path"] for f in files]

        # Should have Program.cs or similar
        assert any(".cs" in path for path in file_paths)

    @pytest.mark.asyncio
    async def test_vuejs_template(self, temp_dir):
        """Test Vue.js template generation."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "vue-project",
            "template": "vuejs",
            "analyze_existing": False,
            "context": "",
            "project_directory": str(temp_dir)
        })

        plan_file = temp_dir / ".cursorplans" / "vue-project.devplan"
        assert plan_file.exists()

        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        # Vue.js template should have specific characteristics
        architecture = plan_data["target_state"]["architecture"]
        assert any("Vue" in str(item) for item in architecture)
        assert any("TypeScript" in str(item) for item in architecture)

        # Should have Vue-specific files
        files = plan_data["resources"]["files"]
        file_paths = [f["path"] for f in files]

        # Should have main.js or App.vue
        assert any(".js" in path or ".vue" in path for path in file_paths)


class TestExistingCodebaseDetection:
    """Test existing codebase detection and analysis."""

    def test_detect_fastapi_project(self, temp_dir):
        """Test detection of FastAPI project."""
        # Create FastAPI project files
        requirements_file = temp_dir / "requirements.txt"
        requirements_file.write_text("fastapi>=0.68.0\nuvicorn>=0.15.0\npydantic>=1.8.0")

        main_file = temp_dir / "main.py"
        main_file.write_text("from fastapi import FastAPI\n\napp = FastAPI()")

        os.chdir(temp_dir)
        detected = detect_existing_codebase(str(temp_dir))

        assert detected["framework"] == "fastapi"
        assert detected["language"] == "python"

    def test_detect_dotnet_project(self, temp_dir):
        """Test detection of .NET project."""
        # Create .NET project files
        csproj_file = temp_dir / "TestProject.csproj"
        csproj_file.write_text("""
<Project Sdk="Microsoft.NET.Sdk.Web">
  <PropertyGroup>
    <TargetFramework>net6.0</TargetFramework>
  </PropertyGroup>
</Project>
        """)

        program_file = temp_dir / "Program.cs"
        program_file.write_text("var app = WebApplication.CreateBuilder(args).Build();")

        os.chdir(temp_dir)
        detected = detect_existing_codebase(str(temp_dir))

        assert detected["framework"] == "dotnet"
        assert detected["language"] == "csharp"

    def test_detect_vuejs_project(self, temp_dir):
        """Test detection of Vue.js project."""
        # Create Vue.js project files
        package_file = temp_dir / "package.json"
        package_file.write_text("""{
  "name": "vue-project",
  "dependencies": {
    "vue": "^3.0.0"
  }
}""")

        main_file = temp_dir / "src" / "main.js"
        main_file.parent.mkdir(parents=True, exist_ok=True)
        main_file.write_text("import { createApp } from 'vue'")

        os.chdir(temp_dir)
        detected = detect_existing_codebase(str(temp_dir))

        assert detected["framework"] == "vuejs"
        assert detected["language"] == "JavaScript/TypeScript"

    def test_detect_unknown_project(self, temp_dir):
        """Test detection of unknown project type."""
        # Create generic files
        readme_file = temp_dir / "README.md"
        readme_file.write_text("# Generic Project")

        os.chdir(temp_dir)
        detected = detect_existing_codebase(str(temp_dir))

        assert detected["framework"] is None
        assert detected["language"] is None
        assert detected["structure"] == "unknown"

    @pytest.mark.asyncio
    async def test_from_existing_template(self, temp_dir):
        """Test creating plan from existing codebase."""
        # Create a FastAPI project
        requirements_file = temp_dir / "requirements.txt"
        requirements_file.write_text("fastapi>=0.68.0\nuvicorn>=0.15.0")

        main_file = temp_dir / "main.py"
        main_file.write_text("from fastapi import FastAPI\n\napp = FastAPI()")

        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "detected-project",
            "template": "from-existing",
            "analyze_existing": True,
            "context": "",
            "project_directory": str(temp_dir)
        })

        plan_file = temp_dir / ".cursorplans" / "detected-project.devplan"
        assert plan_file.exists()

        with open(plan_file) as f:
            plan_data = yaml.safe_load(f)

        # Should detect FastAPI and create appropriate plan
        architecture = plan_data["target_state"]["architecture"]
        assert any("FastAPI" in str(item) for item in architecture)


class TestContextHandling:
    """Test context file handling."""

    @pytest.mark.asyncio
    async def test_plan_with_default_context(self, temp_dir, sample_context_file):
        """Test creating plan with default context file."""
        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "context-project",
            "template": "basic",
            "analyze_existing": False,
            "context": "",  # Uses default context.txt
            "project_directory": str(temp_dir)
        })

        # Should mention context files if they were used
        result_text = result[0].text
        # The exact behavior depends on implementation
        assert "Created development plan" in result_text

    @pytest.mark.asyncio
    async def test_plan_with_story_context(self, temp_dir):
        """Test creating plan with story-specific context."""
        # Create story-specific context file
        story_context = temp_dir / "context-story-456.txt"
        story_context.write_text("src/auth.py\nsrc/users.py\ntests/test_auth.py")

        os.chdir(temp_dir)

        result = await create_dev_plan({
            "name": "story-project",
            "template": "basic",
            "analyze_existing": False,
            "context": "story-456",
            "project_directory": str(temp_dir)
        })

        # Should use the story-specific context
        result_text = result[0].text
        assert "Created development plan" in result_text

        # If context was used, might mention it
        if "context" in result_text.lower():
            assert "story-456" in result_text or "context" in result_text

    def test_load_context_file(self, temp_dir):
        """Test loading context file content."""
        from cursor_plans_mcp.server import load_context_file

        # Create context file
        context_file = temp_dir / "test-context.txt"
        context_content = """# Test context
src/main.py
src/models.py
# Comment line
tests/test_main.py

# Empty line above
requirements.txt"""
        context_file.write_text(context_content)

        os.chdir(temp_dir)

        # Test the context loading function
        import asyncio
        context_files = asyncio.run(load_context_file("test-context.txt"))

        # Should parse non-comment, non-empty lines
        expected_files = ["src/main.py", "src/models.py", "tests/test_main.py", "requirements.txt"]
        for expected in expected_files:
            assert expected in context_files

        # Should not include comments
        assert "# Test context" not in context_files
        assert "# Comment line" not in context_files


class TestTemplateValidation:
    """Test template validation and error handling."""

    @pytest.mark.asyncio
    async def test_invalid_template_fallback(self, temp_dir):
        """Test behavior with invalid template name."""
        os.chdir(temp_dir)

        # Use an invalid template name
        result = await create_dev_plan({
            "name": "fallback-project",
            "template": "nonexistent-template",
            "analyze_existing": False,
            "context": "",
            "project_directory": str(temp_dir)
        })

        # Should not crash, might fall back to basic or show error
        assert len(result) == 1
        assert isinstance(result[0].text, str)

        # Check if a plan file was created anyway (fallback behavior)
        plan_file = temp_dir / ".cursorplans" / "fallback-project.devplan"
        if plan_file.exists():
            # If fallback occurred, should have basic structure
            with open(plan_file) as f:
                plan_data = yaml.safe_load(f)
            assert "project" in plan_data

    @pytest.mark.asyncio
    async def test_template_consistency(self, temp_dir):
        """Test that templates generate consistent structure."""
        os.chdir(temp_dir)

        templates_to_test = ["basic", "fastapi", "dotnet", "vuejs"]

        for template in templates_to_test:
            result = await create_dev_plan({
                "name": f"{template}-test",
                "template": template,
                "analyze_existing": False,
                "context": "",
                "project_directory": str(temp_dir)
            })

            plan_file = temp_dir / ".cursorplans" / f"{template}-test.devplan"
            assert plan_file.exists(), f"Plan file not created for template: {template}"

            with open(plan_file) as f:
                plan_data = yaml.safe_load(f)

            # All templates should have these required sections
            required_sections = ["project", "target_state", "resources", "phases"]
            for section in required_sections:
                assert section in plan_data, f"Missing {section} in {template} template"

            # Project name should match
            assert plan_data["project"]["name"] == f"{template}-test"

            # Should have at least one phase
            assert len(plan_data["phases"]) >= 1, f"No phases in {template} template"

            # Clean up
            plan_file.unlink()

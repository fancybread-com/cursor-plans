"""
Validation result classes for structured validation feedback.
"""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class IssueType(Enum):
    """Types of validation issues."""
    ERROR = "error"          # Blocking issues that prevent plan execution
    WARNING = "warning"      # Best practice violations
    SUGGESTION = "suggestion"  # Improvement recommendations


@dataclass
class ValidationIssue:
    """Represents a single validation issue."""
    type: IssueType
    message: str
    location: str
    suggestion: Optional[str] = None
    can_auto_fix: bool = False

    def format_for_display(self) -> str:
        """Format issue for display in Cursor chat."""
        icon = {
            IssueType.ERROR: "🚫",
            IssueType.WARNING: "⚠️",
            IssueType.SUGGESTION: "💡"
        }[self.type]

        output = f"{icon} **{self.type.value.title()}**: {self.message}\n"
        output += f"   📍 {self.location}\n"

        if self.suggestion:
            output += f"   💡 {self.suggestion}\n"

        return output


class ValidationResult:
    """Results of development plan validation."""

    def __init__(self):
        self.issues: List[ValidationIssue] = []
        self.layers_passed: List[str] = []
        self.layers_failed: List[str] = []

    @property
    def is_valid(self) -> bool:
        """True if no blocking errors exist."""
        return not any(issue.type == IssueType.ERROR for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """True if warnings exist."""
        return any(issue.type == IssueType.WARNING for issue in self.issues)

    @property
    def errors(self) -> List[ValidationIssue]:
        """Get all error-level issues."""
        return [issue for issue in self.issues if issue.type == IssueType.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """Get all warning-level issues."""
        return [issue for issue in self.issues if issue.type == IssueType.WARNING]

    @property
    def suggestions(self) -> List[ValidationIssue]:
        """Get all suggestion-level issues."""
        return [issue for issue in self.issues if issue.type == IssueType.SUGGESTION]

    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue."""
        self.issues.append(issue)

    def add_error(self, message: str, location: str, suggestion: str = None):
        """Add an error-level issue."""
        self.add_issue(ValidationIssue(
            type=IssueType.ERROR,
            message=message,
            location=location,
            suggestion=suggestion
        ))

    def add_warning(self, message: str, location: str, suggestion: str = None):
        """Add a warning-level issue."""
        self.add_issue(ValidationIssue(
            type=IssueType.WARNING,
            message=message,
            location=location,
            suggestion=suggestion
        ))

    def add_suggestion(self, message: str, location: str, suggestion: str = None):
        """Add a suggestion-level issue."""
        self.add_issue(ValidationIssue(
            type=IssueType.SUGGESTION,
            message=message,
            location=location,
            suggestion=suggestion
        ))

    def format_for_cursor(self) -> str:
        """Format validation results for Cursor's chat interface."""
        if not self.issues:
            output = "✅ **Plan validation passed!**\n\n"
            output += "All validation layers completed successfully:\n"
            for layer in self.layers_passed:
                output += f"✅ {layer}\n"
            return output

        # Summary
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        suggestion_count = len(self.suggestions)

        if error_count > 0:
            output = f"❌ **Plan validation failed** ({error_count} errors, {warning_count} warnings)\n\n"
        elif warning_count > 0:
            output = f"⚠️ **Plan validation passed with warnings** ({warning_count} warnings, {suggestion_count} suggestions)\n\n"
        else:
            output = f"✅ **Plan validation passed** ({suggestion_count} suggestions for improvement)\n\n"

        # Validation layers status
        output += "**Validation Layers:**\n"
        for layer in self.layers_passed:
            output += f"✅ {layer}\n"
        for layer in self.layers_failed:
            output += f"❌ {layer}\n"
        output += "\n"

        # Detailed issues
        if self.errors:
            output += "**🚫 Errors (must fix):**\n"
            for error in self.errors:
                output += error.format_for_display() + "\n"

        if self.warnings:
            output += "**⚠️ Warnings (best practices):**\n"
            for warning in self.warnings:
                output += warning.format_for_display() + "\n"

        if self.suggestions:
            output += "**💡 Suggestions (improvements):**\n"
            for suggestion in self.suggestions:
                output += suggestion.format_for_display() + "\n"

        return output

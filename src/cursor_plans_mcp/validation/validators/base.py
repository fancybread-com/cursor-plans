"""
Base validator class for all validation implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from ..results import ValidationResult


class BaseValidator(ABC):
    """Base class for all validators."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this validation layer."""
        pass

    @abstractmethod
    async def validate(
        self, plan_data: Dict[str, Any], plan_file_path: str
    ) -> ValidationResult:
        """
        Validate the development plan.

        Args:
            plan_data: Parsed plan data (YAML as dict)
            plan_file_path: Path to the plan file being validated

        Returns:
            ValidationResult with any issues found
        """
        pass

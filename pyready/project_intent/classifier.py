"""
Deterministic project intent classifier.

Uses ONLY detected capabilities from Phase 7.
No filesystem inspection, no heuristics, no guessing.
"""

from pathlib import Path
from typing import Tuple

from pyready.schemas.capability_schema import ProjectCapabilities
from pyready.project_intent.models import ProjectIntent


class ProjectIntentClassifier:
    """
    Classifies project intent based on detected capabilities.
    
    Rules are deterministic and use first-match-wins logic.
    """
    
    def __init__(self, capabilities: ProjectCapabilities, project_path: Path):
        """
        Initialize classifier.
        
        Args:
            capabilities: Detected project capabilities
            project_path: Path to project (used for .env.example check only)
        """
        self.capabilities = capabilities
        self.project_path = project_path
    
    def classify(self) -> Tuple[ProjectIntent, str]:
        """
        Classify project intent.
        
        Returns:
            (intent, reasoning) tuple
            - intent: Classified ProjectIntent
            - reasoning: Human-readable explanation
        """
        # Rule 1: Not a Python project
        if not self.capabilities.has_python_files:
            return (
                ProjectIntent.UNKNOWN,
                "No Python files detected"
            )
        
        # Rule 2: Script (Python files, no deps, no entry point)
        if (not self.capabilities.has_dependency_declaration and
            not self.capabilities.has_detectable_entrypoint):
            return (
                ProjectIntent.SCRIPT,
                "Python files found, no dependencies or entry point declared"
            )
        
        # Rule 3: Library (deps declared, no entry point)
        if (self.capabilities.has_dependency_declaration and
            not self.capabilities.has_detectable_entrypoint):
            return (
                ProjectIntent.LIBRARY,
                "Dependencies declared, no entry point detected (reusable package)"
            )
        
        # Check for environment variable requirements (needed for SERVICE classification)
        has_env_requirements = self._has_env_requirements()
        
        # Rule 4: Service (entry point + deps + env requirements)
        if (self.capabilities.has_detectable_entrypoint and
            self.capabilities.has_dependency_declaration and
            has_env_requirements):
            return (
                ProjectIntent.SERVICE,
                "Entry point, dependencies, and environment configuration detected"
            )
        
        # Rule 5: Application (entry point + deps, no env requirements)
        if (self.capabilities.has_detectable_entrypoint and
            self.capabilities.has_dependency_declaration):
            return (
                ProjectIntent.APPLICATION,
                "Entry point and dependencies detected, no service configuration"
            )
        
        # Rule 6: Unknown (edge cases)
        # Example: has entry point but no dependencies (unusual)
        return (
            ProjectIntent.UNKNOWN,
            "Capability combination does not match known patterns"
        )
    
    def _has_env_requirements(self) -> bool:
        """
        Check if project declares environment variable requirements.
        
        Evidence:
        - .env.example exists
        - .env.template exists
        
        Returns:
            True if env requirements are declared
        """
        env_example = self.project_path / '.env.example'
        env_template = self.project_path / '.env.template'
        
        return env_example.exists() or env_template.exists()


def classify_project_intent(capabilities: ProjectCapabilities, project_path: Path) -> Tuple[ProjectIntent, str]:
    """
    Classify project intent based on capabilities.
    
    Args:
        capabilities: Detected project capabilities
        project_path: Path to project directory
    
    Returns:
        (intent, reasoning) tuple
    """
    classifier = ProjectIntentClassifier(capabilities, project_path)
    return classifier.classify()

"""
Deterministic recommendation engine.

Generates actionable recommendations based on:
- Project capabilities (Phase 7)
- Project intent (Phase 9)
- Check results (Phase 8)

Rules are explicit, evidence-based, and advisory only.
"""

from typing import List
from pathlib import Path

from pyready.schemas.capability_schema import ProjectCapabilities
from pyready.project_intent.models import ProjectIntent
from pyready.schemas.env_schema import CheckResult, CheckStatus
from pyready.recommendations.models import Recommendation


class RecommendationEngine:
    """
    Generates recommendations based on project state.
    
    All rules are deterministic and evidence-based.
    """
    
    def __init__(
        self,
        capabilities: ProjectCapabilities,
        intent: ProjectIntent,
        check_results: List[CheckResult]
    ):
        """
        Initialize recommendation engine.
        
        Args:
            capabilities: Detected project capabilities
            intent: Classified project intent
            check_results: Results from environment checks
        """
        self.capabilities = capabilities
        self.intent = intent
        self.check_results = check_results
    
    def generate(self) -> List[Recommendation]:
        """
        Generate all applicable recommendations.
        
        Returns:
            List of recommendations (may be empty)
        """
        recommendations = []
        
        # Rule 1: Essential recommendations
        recommendations.extend(self._essential_recommendations())
        
        # Rule 2: Best practice recommendations
        recommendations.extend(self._best_practice_recommendations())
        
        # Rule 3: Check-based recommendations
        recommendations.extend(self._check_based_recommendations())
        
        return recommendations
    
    # =========================================================================
    # Essential Recommendations
    # =========================================================================
    
    def _essential_recommendations(self) -> List[Recommendation]:
        """Generate essential recommendations for project health"""
        recommendations = []
        
        # LIBRARY: Must declare dependencies
        if (self.intent == ProjectIntent.LIBRARY and
            not self.capabilities.has_dependency_declaration):
            recommendations.append(Recommendation(
                title="Declare dependencies for reproducibility",
                description=(
                    "Libraries should declare their dependencies so users can install them. "
                    "This makes your package installable and ensures consistent behavior."
                ),
                evidence=[
                    "Intent: LIBRARY (reusable package)",
                    "No requirements.txt, pyproject.toml, or setup.py found"
                ],
                example_command="Create requirements.txt or setup.py with install_requires"
            ))
        
        # SERVICE: Must have .env.example
        if self.intent == ProjectIntent.SERVICE:
            # Check if .env.example is missing (intent classification already checked this)
            # If intent is SERVICE, .env.example exists, so no recommendation needed
            # This rule triggers if intent would be SERVICE but .env.example is missing
            # However, our intent classifier already requires .env.example for SERVICE
            # So this is a safety check for edge cases
            pass
        
        # APPLICATION with entry point but no deps (unusual)
        if (self.intent == ProjectIntent.APPLICATION and
            self.capabilities.has_detectable_entrypoint and
            not self.capabilities.has_dependency_declaration):
            recommendations.append(Recommendation(
                title="Consider declaring dependencies",
                description=(
                    "Applications with entry points typically have dependencies. "
                    "Declaring them ensures others can run your application."
                ),
                evidence=[
                    "Intent: APPLICATION (standalone app)",
                    "Entry point detected",
                    "No dependency declaration found"
                ],
                example_command="Create requirements.txt listing your dependencies"
            ))
        
        return recommendations
    
    # =========================================================================
    # Best Practice Recommendations
    # =========================================================================
    
    def _best_practice_recommendations(self) -> List[Recommendation]:
        """Generate best practice recommendations"""
        recommendations = []
        
        # Virtual environment for applications and services
        if (self.intent in [ProjectIntent.APPLICATION, ProjectIntent.SERVICE] and
            self.capabilities.has_dependency_declaration and
            not self.capabilities.has_isolated_environment):
            recommendations.append(Recommendation(
                title="Create a virtual environment",
                description=(
                    "Virtual environments isolate your project's dependencies from other projects. "
                    "This prevents version conflicts and makes your setup reproducible."
                ),
                evidence=[
                    f"Intent: {self.intent.value.upper()}",
                    "Dependencies declared",
                    "No virtual environment detected"
                ],
                example_command="python -m venv venv"
            ))
        
        # Reproducible environment (lock files or pinned versions)
        if (self.intent in [ProjectIntent.LIBRARY, ProjectIntent.APPLICATION, ProjectIntent.SERVICE] and
            self.capabilities.has_dependency_declaration and
            not self.capabilities.has_reproducible_environment):
            recommendations.append(Recommendation(
                title="Pin dependency versions for reproducibility",
                description=(
                    "Lock files or pinned versions ensure your project works the same way "
                    "across different environments and over time."
                ),
                evidence=[
                    f"Intent: {self.intent.value.upper()}",
                    "Dependencies declared",
                    "No poetry.lock, Pipfile.lock, or pinned versions (==) in requirements.txt"
                ],
                example_command="Use poetry add or pip freeze > requirements.txt"
            ))
        
        # Python version specification
        if (self.intent in [ProjectIntent.LIBRARY, ProjectIntent.APPLICATION, ProjectIntent.SERVICE] and
            self.capabilities.has_dependency_declaration and
            self._no_python_version_specified()):
            recommendations.append(Recommendation(
                title="Specify Python version requirement",
                description=(
                    "Declaring the required Python version prevents compatibility issues "
                    "and helps users know what Python version to use."
                ),
                evidence=[
                    f"Intent: {self.intent.value.upper()}",
                    "No Python version requirement in pyproject.toml"
                ],
                example_command="Add 'python = \"^3.9\"' to pyproject.toml [tool.poetry.dependencies]"
            ))
        
        # Environment variable documentation for services
        if (self.intent == ProjectIntent.APPLICATION and
            self.capabilities.has_detectable_entrypoint and
            self._has_env_file_but_no_example()):
            recommendations.append(Recommendation(
                title="Document environment variables with .env.example",
                description=(
                    "Your project uses environment variables. Creating .env.example documents "
                    "required variables for other developers."
                ),
                evidence=[
                    "Intent: APPLICATION",
                    ".env file found",
                    "No .env.example or .env.template found"
                ],
                example_command="Copy .env to .env.example and remove sensitive values"
            ))
        
        return recommendations
    
    # =========================================================================
    # Check-Based Recommendations
    # =========================================================================
    
    def _check_based_recommendations(self) -> List[Recommendation]:
        """Generate recommendations based on check results"""
        recommendations = []
        
        # Dependency verification warning
        dep_check = self._find_check("Dependencies")
        if dep_check and dep_check.status == CheckStatus.WARN:
            if "cannot verify" in dep_check.message.lower():
                recommendations.append(Recommendation(
                    title="Enable dependency verification",
                    description=(
                        "Dependencies are declared but cannot be verified without a virtual environment. "
                        "Creating a venv allows PyReady to check for missing packages."
                    ),
                    evidence=[
                        "Check result: Dependencies - WARN",
                        dep_check.details or "Cannot verify without isolated environment"
                    ],
                    example_command="python -m venv venv && venv\\Scripts\\activate (Windows) or source venv/bin/activate (Unix)"
                ))
        
        # Virtual environment warning - REMOVED to prevent duplicates
        # Best practice recommendation already covers virtual environment creation
        
        return recommendations
    
    # =========================================================================
    # Helper Methods
    # =========================================================================
    
    def _find_check(self, category: str) -> CheckResult:
        """Find check result by category"""
        for check in self.check_results:
            if check.category == category:
                return check
        return None
    
    def _no_python_version_specified(self) -> bool:
        """Check if Python version check returned INFO status"""
        python_check = self._find_check("Python Version")
        if python_check:
            return python_check.status == CheckStatus.INFO
        return False
    
    def _has_env_file_but_no_example(self) -> bool:
        """Check if .env exists but .env.example doesn't"""
        env_check = self._find_check("Environment Variables")
        if env_check:
            # Only recommend if .env file was explicitly found
            if (env_check.status == CheckStatus.PASS and 
                ".env found" in env_check.message):
                # .env exists, and we know .env.example doesn't 
                # (intent is APPLICATION not SERVICE)
                return True
        return False

def generate_recommendations(
    capabilities: ProjectCapabilities,
    intent: ProjectIntent,
    check_results: List[CheckResult]
) -> List[Recommendation]:
    """
    Generate recommendations for a project.
    
    Args:
        capabilities: Detected project capabilities
        intent: Classified project intent
        check_results: Results from environment checks
    
    Returns:
        List of recommendations (may be empty)
    """
    engine = RecommendationEngine(capabilities, intent, check_results)
    return engine.generate()

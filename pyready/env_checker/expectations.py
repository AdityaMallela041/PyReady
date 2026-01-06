"""
Expectation policy layer for capability-aware environment checking.

This module decides:
- Whether a check should run
- What severity to use (FAIL vs WARN)
- What message to display

Rules are deterministic and based on detected capabilities only.
"""

from typing import Tuple, Optional
from pyready.schemas.capability_schema import ProjectCapabilities


class CheckExpectations:
    """
    Determines check expectations based on project capabilities.
    
    Principle: Capabilities are observations, not requirements.
    A check should FAIL only when a declared requirement is provably broken.
    """
    
    def __init__(self, capabilities: ProjectCapabilities):
        self.capabilities = capabilities
    
    # ========================================================================
    # Python Version Check
    # ========================================================================
    
    def should_check_python_version(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if Python version check should run.
        
        Returns:
            (should_run, skip_reason)
            - should_run: True if check applies
            - skip_reason: Explanation if skipped
        """
        if not self.capabilities.has_python_files:
            return (False, "No Python files detected, version check not applicable")
        
        return (True, None)
    
    def python_version_no_requirement_status(self) -> str:
        """
        When Python files exist but no version requirement is declared.
        
        Returns:
            Status to use: "INFO"
        """
        return "INFO"
    
    # ========================================================================
    # Virtual Environment Check
    # ========================================================================
    
    def should_check_virtual_environment(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if virtual environment check should run.
        
        Logic:
        - Virtual environment is expected when dependencies are declared
        - If no dependencies declared, venv is not required
        
        Returns:
            (should_run, skip_reason)
        """
        if not self.capabilities.has_dependency_declaration:
            return (False, "No dependencies declared, virtual environment not required")
        
        return (True, None)
    
    def virtual_environment_missing_severity(self) -> str:
        """
        When venv is expected but not found.
        
        Returns:
            "WARN" - Recommended but not critical
        """
        return "WARN"
    
    # ========================================================================
    # Dependencies Check
    # ========================================================================
    
    def should_check_dependencies(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if dependency check should run.
        
        Logic:
        - Can only check if dependencies are declared
        - If no declaration, nothing to verify
        
        Returns:
            (should_run, skip_reason)
        """
        if not self.capabilities.has_dependency_declaration:
            return (False, "No dependency declaration found, check not applicable")
        
        return (True, None)
    
    def dependencies_cannot_verify_severity(self) -> str:
        """
        When dependencies are declared but cannot be verified.
        
        Reason: No isolated environment to run pip list in
        
        Returns:
            "WARN" - Cannot prove failure without venv
        """
        return "WARN"
    
    def can_verify_dependencies(self) -> bool:
        """
        Check if dependencies can actually be verified.
        
        Requires:
        - Dependency declaration exists
        - Isolated environment exists (to run pip list)
        
        Returns:
            True if verification is possible
        """
        return (
            self.capabilities.has_dependency_declaration and
            self.capabilities.has_isolated_environment
        )
    
    # ========================================================================
    # Environment Variables Check
    # ========================================================================
    
    def should_check_environment_variables(self) -> Tuple[bool, Optional[str]]:
        """
        Determine if environment variables check should run.
        
        Logic:
        - Always runs (no capability dependency)
        - Whether requirements exist is determined by .env.example presence
        
        Returns:
            (True, None) - Always applicable
        """
        return (True, None)


def create_skip_result(category: str, skip_reason: str) -> dict:
    """
    Create a check result for a skipped check.
    
    Args:
        category: Check category name
        skip_reason: Why the check was skipped
    
    Returns:
        dict with status="INFO" and skip message
    """
    return {
        "status": "INFO",
        "message": f"Check skipped",
        "details": skip_reason,
        "fix_command": None
    }


def downgrade_to_warn(original_result: dict, reason: str) -> dict:
    """
    Downgrade a FAIL result to WARN.
    
    Args:
        original_result: Original check result
        reason: Why it was downgraded
    
    Returns:
        Modified result with WARN status
    """
    return {
        "status": "WARN",
        "message": original_result.get("message", ""),
        "details": reason,
        "fix_command": original_result.get("fix_command")
    }

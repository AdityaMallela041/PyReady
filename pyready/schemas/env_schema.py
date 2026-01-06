"""Environment check schemas"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CheckStatus(Enum):
    """Status of an environment check"""
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    INFO = "INFO"


class CheckResult(BaseModel):
    """Result of a single environment check"""
    category: str = Field(description="Category of the check (e.g., 'Python Version')")
    status: CheckStatus = Field(description="Status of the check")
    message: str = Field(description="Human-readable message")
    details: Optional[str] = Field(None, description="Additional details or context")
    fix_command: Optional[str] = Field(None, description="Suggested command to fix the issue")


class EnvironmentCheckReport(BaseModel):
    """Complete environment check report for a repository"""
    repo_path: str = Field(description="Path to the repository")
    os_type: str = Field(description="Operating system type")
    checks: List[CheckResult] = Field(description="List of check results")
    summary: dict = Field(description="Summary statistics")

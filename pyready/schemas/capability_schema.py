"""Project capability detection schema"""

from typing import Dict, List
from pydantic import BaseModel, Field


class ProjectCapabilities(BaseModel):
    """
    Evidence-based model of what can be determined about a project.
    
    Each capability is derived from filesystem evidence only.
    False means "not detected", not "does not exist".
    """
    
    has_python_files: bool = Field(
        description="Python source files (.py) found in project"
    )
    
    has_dependency_declaration: bool = Field(
        description="Dependency specification file found (requirements.txt, pyproject.toml, setup.py, Pipfile)"
    )
    
    has_isolated_environment: bool = Field(
        description="Virtual environment directory found (venv/, .venv/, env/)"
    )
    
    has_reproducible_environment: bool = Field(
        description="Environment can be recreated from declarations (lock files, pinned versions)"
    )
    
    has_detectable_entrypoint: bool = Field(
        description="Entry point can be determined (scripts, __main__, app instance)"
    )
    
    evidence: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="File paths and markers supporting each capability"
    )
    
    class Config:
        frozen = True


class CapabilityCheckResult(BaseModel):
    """Result of capability detection for a project"""
    
    project_path: str
    capabilities: ProjectCapabilities
    warnings: List[str] = Field(default_factory=list)

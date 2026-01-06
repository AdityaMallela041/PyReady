# onboardai/project_detection/detector.py
"""Core project type detection logic."""

from pathlib import Path

from .evidence import (
    has_poetry_pyproject,
    has_requirements_files,
    has_setuptools_files,
)
from .models import ProjectType


def detect_project_type(project_root: Path) -> ProjectType:
    """Detect project type based on filesystem evidence.
    
    Detection follows strict priority order (first match wins):
    1. POETRY - pyproject.toml with [tool.poetry]
    2. PIP_VENV - requirements.txt or requirements/*.txt
    3. SETUPTOOLS - setup.py or setup.cfg
    4. UNKNOWN - none of the above
    
    This function is deterministic and has no side effects.
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        ProjectType enum value representing the detected project type
    """
    if not project_root.exists() or not project_root.is_dir():
        return ProjectType.UNKNOWN
    
    # Priority 1: Poetry
    if has_poetry_pyproject(project_root):
        return ProjectType.POETRY
    
    # Priority 2: Pip + venv
    if has_requirements_files(project_root):
        return ProjectType.PIP_VENV
    
    # Priority 3: Setuptools
    if has_setuptools_files(project_root):
        return ProjectType.SETUPTOOLS
    
    # Fallback: Unknown
    return ProjectType.UNKNOWN

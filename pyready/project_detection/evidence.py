# onboardai/project_detection/evidence.py
"""Evidence collection helpers for project type detection.

All functions are deterministic and based on filesystem checks only.
"""

from pathlib import Path


def has_poetry_pyproject(root: Path) -> bool:
    """Check if project has Poetry configuration.
    
    Evidence: pyproject.toml exists AND contains [tool.poetry] section.
    
    Args:
        root: Project root directory
        
    Returns:
        True if Poetry project detected, False otherwise
    """
    pyproject = root / "pyproject.toml"
    if not pyproject.exists():
        return False
    
    try:
        content = pyproject.read_text(encoding="utf-8")
        return "[tool.poetry]" in content
    except (OSError, UnicodeDecodeError):
        return False


def has_requirements_files(root: Path) -> bool:
    """Check if project has pip requirements files.
    
    Evidence: Any of the following exist:
    - requirements.txt
    - requirements-dev.txt
    - requirements/*.txt
    
    Args:
        root: Project root directory
        
    Returns:
        True if requirements files found, False otherwise
    """
    # Check root-level requirements files
    if (root / "requirements.txt").exists():
        return True
    
    if (root / "requirements-dev.txt").exists():
        return True
    
    # Check requirements/ directory
    requirements_dir = root / "requirements"
    if requirements_dir.is_dir():
        txt_files = list(requirements_dir.glob("*.txt"))
        if txt_files:
            return True
    
    return False


def has_setuptools_files(root: Path) -> bool:
    """Check if project has setuptools configuration.
    
    Evidence: Any of the following exist:
    - setup.py
    - setup.cfg
    
    Args:
        root: Project root directory
        
    Returns:
        True if setuptools files found, False otherwise
    """
    if (root / "setup.py").exists():
        return True
    
    if (root / "setup.cfg").exists():
        return True
    
    return False

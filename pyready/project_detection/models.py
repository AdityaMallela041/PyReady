# onboardai/project_detection/models.py
"""Data models for project type detection."""

from enum import Enum


class ProjectType(str, Enum):
    """Detected project type based on filesystem evidence.
    
    Detection priority (first match wins):
    1. POETRY - pyproject.toml with [tool.poetry]
    2. PIP_VENV - requirements.txt or requirements/*.txt
    3. SETUPTOOLS - setup.py or setup.cfg
    4. UNKNOWN - none of the above
    """
    
    POETRY = "poetry"
    PIP_VENV = "pip_venv"
    SETUPTOOLS = "setuptools"
    UNKNOWN = "unknown"

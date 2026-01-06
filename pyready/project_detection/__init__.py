# onboardai/project_detection/__init__.py
"""Project type detection module.

Deterministically detects Python project types based on filesystem evidence only.
"""

from .detector import detect_project_type
from .models import ProjectType

__all__ = ["detect_project_type", "ProjectType"]

"""Project intent classification models"""

from enum import Enum


class ProjectIntent(Enum):
    """
    Classification of project's intended purpose.
    
    Derived deterministically from detected capabilities only.
    Not a judgment — just a classification.
    """
    
    SCRIPT = "script"
    """Single-file or simple Python scripts with no dependencies"""
    
    LIBRARY = "library"
    """Reusable package with dependencies but no entry point"""
    
    APPLICATION = "application"
    """Standalone application with entry point, no service requirements"""
    
    SERVICE = "service"
    """Application that requires environment configuration (APIs, databases, etc.)"""
    
    UNKNOWN = "unknown"
    """Cannot determine intent from available evidence"""
    
    def __str__(self) -> str:
        """Human-readable name"""
        return self.value.capitalize()

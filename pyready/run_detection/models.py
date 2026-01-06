"""Data models for run command detection."""

from dataclasses import dataclass
from typing import List, Optional
from enum import Enum


class RunCommandType(Enum):
    """Types of run commands that can be detected."""
    POETRY_SCRIPT = "poetry_script"
    FASTAPI = "fastapi"
    FLASK = "flask"
    DIRECT_PYTHON = "direct_python"
    NONE = "none"


class DetectionBasis(Enum):
    """Basis for detection decision."""
    EXPLICIT = "explicit"          # Poetry script defined by developer
    PATTERN_BASED = "pattern-based"  # Framework pattern detected
    FALLBACK = "fallback"          # __main__ entry point
    NONE = "none"                  # No detection


@dataclass
class EvidenceItem:
    """Single piece of evidence for run command detection."""
    file_path: str
    reason: str
    line_number: Optional[int] = None
    
    def __str__(self) -> str:
        if self.line_number:
            return f"{self.file_path}:{self.line_number}: {self.reason}"
        return f"{self.file_path}: {self.reason}"


@dataclass
class RunCommandResult:
    """Result of run command detection."""
    command: Optional[str]
    command_type: RunCommandType
    evidence: List[EvidenceItem]
    detection_basis: DetectionBasis  # Replaced "confidence"
    
    def has_command(self) -> bool:
        """Check if a valid command was detected."""
        return self.command is not None and self.command_type != RunCommandType.NONE

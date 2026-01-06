"""Deterministic question classification."""

from enum import Enum
from typing import Optional, Tuple
import re


class QuestionType(Enum):
    """Supported question types."""
    WHY_REQUIRED = "why_required"           # "Why is X required?"
    WHAT_RUNS = "what_runs"                 # "What runs when I start the project?"
    WHAT_BREAKS = "what_breaks"             # "What breaks if I remove X?"
    WHERE_USED = "where_used"               # "Where is X used?"
    UNSUPPORTED = "unsupported"             # Question type not supported


class QuestionClassifier:
    """
    Deterministically classifies questions into supported types.
    
    Uses pattern matching, NOT AI/LLM inference.
    """
    
    def __init__(self):
        """Initialize classifier with question patterns."""
        # Patterns for "Why is X required?"
        self.why_required_patterns = [
            r"why\s+is\s+(\w+)\s+required",
            r"why\s+do\s+(?:i|we)\s+need\s+(\w+)",
            r"what\s+is\s+(\w+)\s+used\s+for",
            r"what\s+does\s+(\w+)\s+do",
            r"why\s+(\w+)",
        ]
        
        # Patterns for "What runs when I start?"
        self.what_runs_patterns = [
            r"what\s+runs\s+when\s+(?:i|we)\s+start",
            r"what\s+happens\s+when\s+(?:i|we)\s+(?:run|start)",
            r"what\s+is\s+the\s+entry\s+point",
            r"how\s+do\s+(?:i|we)\s+(?:run|start)\s+(?:the|this)\s+project",
            r"what\s+command\s+(?:do|should)\s+(?:i|we)\s+run",
        ]
        
        # Patterns for "What breaks if I remove X?"
        self.what_breaks_patterns = [
            r"what\s+breaks\s+if\s+(?:i|we)\s+remove\s+(\w+)",
            r"what\s+depends\s+on\s+(\w+)",
            r"what\s+uses\s+(\w+)",
            r"can\s+(?:i|we)\s+remove\s+(\w+)",
            r"is\s+(\w+)\s+(?:safe|okay)\s+to\s+remove",
        ]
        
        # Patterns for "Where is X used?"
        self.where_used_patterns = [
            r"where\s+is\s+(\w+)\s+used",
            r"where\s+(?:do|does)\s+(?:we|i)\s+use\s+(\w+)",
            r"which\s+files\s+use\s+(\w+)",
            r"which\s+modules\s+import\s+(\w+)",
        ]
    
    def classify(self, question: str) -> Tuple[QuestionType, Optional[str]]:
        """
        Classify question into supported type.
        
        Args:
            question: User's question string
            
        Returns:
            Tuple of (QuestionType, extracted_entity)
            extracted_entity is None for WHAT_RUNS and UNSUPPORTED types
        """
        # Normalize question
        normalized = question.lower().strip()
        
        # Remove trailing question mark
        normalized = normalized.rstrip("?")
        
        # Try "Why is X required?" patterns
        for pattern in self.why_required_patterns:
            match = re.search(pattern, normalized)
            if match:
                entity = match.group(1) if match.lastindex else None
                return (QuestionType.WHY_REQUIRED, entity)
        
        # Try "What runs when I start?" patterns
        for pattern in self.what_runs_patterns:
            if re.search(pattern, normalized):
                return (QuestionType.WHAT_RUNS, None)
        
        # Try "What breaks if I remove X?" patterns
        for pattern in self.what_breaks_patterns:
            match = re.search(pattern, normalized)
            if match:
                entity = match.group(1) if match.lastindex else None
                return (QuestionType.WHAT_BREAKS, entity)
        
        # Try "Where is X used?" patterns
        for pattern in self.where_used_patterns:
            match = re.search(pattern, normalized)
            if match:
                entity = match.group(1) if match.lastindex else None
                return (QuestionType.WHERE_USED, entity)
        
        # No pattern matched
        return (QuestionType.UNSUPPORTED, None)

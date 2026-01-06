"""Recommendation models"""

from typing import List, Optional
from pydantic import BaseModel, Field


class Recommendation(BaseModel):
    """
    A single recommendation for improving a project.
    
    Recommendations are deterministic, evidence-based, and advisory only.
    """
    
    title: str = Field(
        description="Short title of the recommendation"
    )
    
    description: str = Field(
        description="Detailed explanation of why this is recommended"
    )
    
    evidence: List[str] = Field(
        description="Filesystem evidence or check results supporting this recommendation"
    )
    
    example_command: Optional[str] = Field(
        None,
        description="Optional safe, generic command example"
    )
    
    class Config:
        frozen = True

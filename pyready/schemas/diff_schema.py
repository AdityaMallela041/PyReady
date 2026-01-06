"""Diff schema for comparing two PyReady reports"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class DiffItem(BaseModel):
    """
    A single change detected between two reports.
    
    Pure comparison - no interpretation or scoring.
    """
    
    section: str = Field(
        description="Which section changed (capabilities, intent, checks, recommendations, run_command)"
    )
    
    key: str = Field(
        description="Identifier for what changed (e.g., check category, capability name)"
    )
    
    change_type: str = Field(
        description="Type of change: added | removed | changed"
    )
    
    before: Optional[str] = Field(
        None,
        description="Value before change (null for 'added')"
    )
    
    after: Optional[str] = Field(
        None,
        description="Value after change (null for 'removed')"
    )
    
    class Config:
        frozen = True


class OnboardAIDiffReport(BaseModel):
    """
    Complete diff between two PyReady reports.
    
    This is pure comparison - no interpretation, scoring, or severity.
    """
    
    from_report: str = Field(
        description="Timestamp or identifier of the old report"
    )
    
    to_report: str = Field(
        description="Timestamp or identifier of the new report"
    )
    
    generated_at: datetime = Field(
        description="When this diff was generated (UTC)"
    )
    
    changes: List[DiffItem] = Field(
        description="List of all detected changes (stable ordering)"
    )
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

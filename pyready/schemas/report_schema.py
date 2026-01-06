"""Report schema for OnboardAI output serialization"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from pyready.schemas.capability_schema import ProjectCapabilities
from pyready.schemas.env_schema import CheckResult, CheckStatus
from pyready.recommendations.models import Recommendation


class OnboardAIReport(BaseModel):
    """
    Complete report of an OnboardAI check run.
    
    This is a pure serialization of already-computed results.
    No additional computation or intelligence is performed.
    """
    
    tool_version: str = Field(
        description="OnboardAI version that generated this report"
    )
    
    generated_at: datetime = Field(
        description="Timestamp when this report was generated (UTC)"
    )
    
    project_path: str = Field(
        description="Absolute path to the project that was checked"
    )
    
    project_type: str = Field(
        description="Detected project type (poetry, pip_venv, npm, unknown)"
    )
    
    project_intent: str = Field(
        description="Classified project intent (script, library, application, service, unknown)"
    )
    
    capabilities: ProjectCapabilities = Field(
        description="Detected project capabilities"
    )
    
    checks: List[CheckResult] = Field(
        description="Environment check results"
    )
    
    recommendations: List[Recommendation] = Field(
        description="Generated recommendations for improvement"
    )
    
    run_command: Optional[str] = Field(
        None,
        description="Detected run command (if any)"
    )
    
    run_command_evidence: Optional[List[str]] = Field(
        None,
        description="Evidence supporting the detected run command"
    )
    
    class Config:
        # Use enum values for JSON serialization
        use_enum_values = True
        
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            CheckStatus: lambda v: v.value  # Serialize enum to string
        }

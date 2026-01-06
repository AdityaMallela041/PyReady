"""Policy explanation schema for tracing evaluation decisions"""

from typing import List, Optional
from pydantic import BaseModel, Field


class RuleEvaluationTrace(BaseModel):
    """
    Trace of a single rule evaluation.
    
    Explains what happened when evaluating one rule against the diff.
    Pure traceability - no interpretation.
    """
    
    rule_id: str = Field(
        description="Unique identifier of the rule"
    )
    
    description: str = Field(
        description="Human-readable description from policy file"
    )
    
    evaluated: bool = Field(
        description="Whether this rule was evaluated (false if disabled)"
    )
    
    matched: bool = Field(
        description="Whether this rule matched any diff items"
    )
    
    action: Optional[str] = Field(
        None,
        description="Action if matched: FAIL | WARN | None (if not matched or disabled)"
    )
    
    matched_changes: List[str] = Field(
        default_factory=list,
        description="Keys of DiffItems that matched this rule"
    )
    
    reason: str = Field(
        description="Plain-English explanation of why this rule did or did not match"
    )


class PolicyExplanation(BaseModel):
    """
    Complete explanation of policy evaluation.
    
    Traces every rule to explain the overall decision.
    Deterministic - same input produces same explanation.
    """
    
    overall_status: str = Field(
        description="Final policy status: PASS | WARN | FAIL"
    )
    
    total_rules: int = Field(
        description="Total number of rules in policy"
    )
    
    rules_evaluated: int = Field(
        description="Number of rules that were evaluated (enabled)"
    )
    
    rules_matched: int = Field(
        description="Number of rules that matched diff items"
    )
    
    rules: List[RuleEvaluationTrace] = Field(
        description="Evaluation trace for each rule (in policy file order)"
    )
    
    class Config:
        json_encoders = {
            # Ensure consistent serialization
        }

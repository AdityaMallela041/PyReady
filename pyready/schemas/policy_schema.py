"""Policy schema for evaluating diffs against rules"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field

from pyready.schemas.diff_schema import DiffItem


class PolicyRuleCondition(BaseModel):
    """
    Conditions that must match for a rule to trigger.
    
    Pure pattern matching - no interpretation.
    """
    
    section: Optional[str] = Field(
        None,
        description="Section to match (capabilities, intent, checks, recommendations, run_command)"
    )
    
    key: Optional[str] = Field(
        None,
        description="Specific key to match (can use wildcards with *)"
    )
    
    change_type: Optional[str] = Field(
        None,
        description="Change type to match: added | removed | changed"
    )
    
    field: Optional[str] = Field(
        None,
        description="Field name within key (e.g., 'status' for checks)"
    )
    
    from_values: Optional[List[str]] = Field(
        None,
        alias="from",
        description="Before values that trigger rule"
    )
    
    to_values: Optional[List[str]] = Field(
        None,
        alias="to",
        description="After values that trigger rule"
    )
    
    class Config:
        populate_by_name = True


class PolicyRule(BaseModel):
    """
    A single policy rule.
    
    Declarative and deterministic - no heuristics.
    """
    
    id: str = Field(
        description="Unique rule identifier"
    )
    
    description: str = Field(
        description="Human-readable description of what this rule enforces"
    )
    
    when: PolicyRuleCondition = Field(
        description="Conditions that trigger this rule"
    )
    
    action: Literal["FAIL", "WARN"] = Field(
        description="Action to take when rule matches"
    )
    
    enabled: bool = Field(
        True,
        description="Whether this rule is active"
    )


class PolicyDefinition(BaseModel):
    """
    Complete policy definition.
    
    Loaded from .pyready-policy.yml or .onboardai-policy.json
    """
    
    version: int = Field(
        description="Policy schema version (currently 1)"
    )
    
    rules: List[PolicyRule] = Field(
        description="List of policy rules to evaluate"
    )


class PolicyViolation(BaseModel):
    """
    A detected policy violation.
    
    Links a rule to the diff item that triggered it.
    """
    
    rule_id: str = Field(
        description="ID of the violated rule"
    )
    
    rule_description: str = Field(
        description="Description of the violated rule"
    )
    
    action: Literal["FAIL", "WARN"] = Field(
        description="Action specified by the rule"
    )
    
    diff_item: DiffItem = Field(
        description="The diff item that triggered this violation"
    )


class PolicyEvaluationResult(BaseModel):
    """
    Result of evaluating a diff against a policy.
    
    Deterministic: same diff + same policy → same result.
    """
    
    status: Literal["PASS", "WARN", "FAIL"] = Field(
        description="Overall evaluation status (FAIL > WARN > PASS)"
    )
    
    violations: List[PolicyViolation] = Field(
        description="All detected violations"
    )
    
    rules_evaluated: int = Field(
        description="Number of rules evaluated"
    )
    
    changes_checked: int = Field(
        description="Number of diff items checked"
    )

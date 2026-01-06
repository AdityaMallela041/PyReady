"""
Policy evaluation engine.

Pure rule matching - no heuristics, scoring, or interpretation.
"""

import json
import yaml
from pathlib import Path
from typing import Optional
import fnmatch

from pyready.schemas.diff_schema import OnboardAIDiffReport, DiffItem
from pyready.schemas.policy_schema import (
    PolicyDefinition,
    PolicyRule,
    PolicyViolation,
    PolicyEvaluationResult
)


def load_policy(policy_path: Path) -> PolicyDefinition:
    """
    Load policy from YAML or JSON file.
    
    Args:
        policy_path: Path to policy file
    
    Returns:
        Parsed PolicyDefinition
    
    Raises:
        ValueError: If file format is invalid
    """
    if not policy_path.exists():
        raise FileNotFoundError(f"Policy file not found: {policy_path}")
    
    suffix = policy_path.suffix.lower()
    
    try:
        with open(policy_path, 'r', encoding='utf-8') as f:
            if suffix in ['.yml', '.yaml']:
                data = yaml.safe_load(f)
            elif suffix == '.json':
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported policy file format: {suffix}")
        
        return PolicyDefinition(**data)
    
    except Exception as e:
        raise ValueError(f"Failed to load policy: {e}")


def evaluate_policy(
    diff: OnboardAIDiffReport,
    policy: PolicyDefinition
) -> PolicyEvaluationResult:
    """
    Evaluate a diff report against a policy.
    
    Pure rule evaluation - no interpretation or scoring.
    
    Args:
        diff: Diff report from Phase 12
        policy: Policy definition to evaluate against
    
    Returns:
        PolicyEvaluationResult with violations and status
    """
    violations = []
    
    # Get only enabled rules
    enabled_rules = [rule for rule in policy.rules if rule.enabled]
    
    # Check each diff item against each rule
    for diff_item in diff.changes:
        for rule in enabled_rules:
            if _rule_matches(rule, diff_item):
                violations.append(PolicyViolation(
                    rule_id=rule.id,
                    rule_description=rule.description,
                    action=rule.action,
                    diff_item=diff_item
                ))
    
    # Determine overall status: FAIL > WARN > PASS
    status = "PASS"
    if violations:
        if any(v.action == "FAIL" for v in violations):
            status = "FAIL"
        else:
            status = "WARN"
    
    return PolicyEvaluationResult(
        status=status,
        violations=violations,
        rules_evaluated=len(enabled_rules),
        changes_checked=len(diff.changes)
    )


def _rule_matches(rule: PolicyRule, diff_item: DiffItem) -> bool:
    """
    Check if a rule matches a diff item.
    
    Pure pattern matching - all conditions must match (AND logic).
    
    Args:
        rule: Policy rule to check
        diff_item: Diff item to match against
    
    Returns:
        True if rule matches, False otherwise
    """
    condition = rule.when
    
    # Check section match
    if condition.section is not None:
        if diff_item.section != condition.section:
            return False
    
    # Check key match (supports wildcards)
    if condition.key is not None:
        if not fnmatch.fnmatch(diff_item.key, condition.key):
            return False
    
    # Check change_type match
    if condition.change_type is not None:
        if diff_item.change_type != condition.change_type:
            return False
    
    # Check field-specific matching for checks
    # Field is embedded in the key (e.g., "Dependencies_status")
    if condition.field is not None:
        if not diff_item.key.endswith(f"_{condition.field}"):
            return False
    
    # Check from values
    if condition.from_values is not None:
        if diff_item.before is None:
            return False
        
        # Extract value from before string
        before_value = _extract_value(diff_item.before)
        if before_value not in condition.from_values:
            return False
    
    # Check to values
    if condition.to_values is not None:
        if diff_item.after is None:
            return False
        
        # Extract value from after string
        after_value = _extract_value(diff_item.after)
        if after_value not in condition.to_values:
            return False
    
    # All conditions matched
    return True


def _extract_value(value_str: str) -> str:
    """
    Extract the actual value from a diff string.
    
    Examples:
        "WARN" → "WARN"
        "Status: PASS" → "PASS"
        "Virtual environment: found" → "found"
    
    Args:
        value_str: Value string from diff item
    
    Returns:
        Extracted value (or original if no extraction needed)
    """
    # If it's a simple value (single word), return as-is
    if ' ' not in value_str and ':' not in value_str:
        return value_str
    
    # Try to extract from "key: value" format
    if ':' in value_str:
        parts = value_str.split(':', 1)
        if len(parts) == 2:
            return parts[1].strip()
    
    # Try to extract last word (for "Status: PASS" → "PASS")
    words = value_str.split()
    if words:
        return words[-1]
    
    # Return original if no pattern matches
    return value_str

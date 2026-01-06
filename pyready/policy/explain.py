"""
Policy explanation engine.

Traces why policy decisions were made without re-evaluating anything.
Pure explainability - no logic changes.

IMPORTANT: Policy explanations are FULLY DETERMINISTIC and do NOT use Groq or any LLM.
This ensures policy decisions are reproducible, auditable, and CI/CD safe.
Same input always produces the same explanation (character-for-character identical).

This separation is critical:
- Policy explanations (this module) = Deterministic rule-based templates
- Run command explanations (cli/explain.py) = Optional Groq enhancement
"""

from typing import List, Dict, Set

from pyready.schemas.diff_schema import OnboardAIDiffReport, DiffItem
from pyready.schemas.policy_schema import PolicyDefinition, PolicyRule, PolicyEvaluationResult
from pyready.schemas.policy_explain_schema import RuleEvaluationTrace, PolicyExplanation
from pyready.policy.engine import _rule_matches


def explain_policy(
    diff: OnboardAIDiffReport,
    policy: PolicyDefinition,
    evaluation: PolicyEvaluationResult
) -> PolicyExplanation:
    """
    Generate explanation for policy evaluation.
    
    Traces every rule to explain why the overall status was reached.
    Does NOT re-evaluate - uses existing evaluation result.
    
    DETERMINISM GUARANTEE:
    - Same diff + same policy + same evaluation = same explanation (always)
    - No network calls, no API dependencies, no variation
    - Suitable for audit logs, regression testing, CI/CD output caching
    
    Args:
        diff: Diff report that was evaluated
        policy: Policy definition that was applied
        evaluation: Result of policy evaluation
    
    Returns:
        PolicyExplanation with traces for all rules
    """
    
    # Build violation lookup for quick access
    violations_by_rule = _build_violation_lookup(evaluation)
    
    # Trace each rule in policy file order
    traces = []
    rules_evaluated = 0
    rules_matched = 0
    
    for rule in policy.rules:
        trace = _trace_rule(rule, diff, violations_by_rule)
        traces.append(trace)
        
        if trace.evaluated:
            rules_evaluated += 1
        if trace.matched:
            rules_matched += 1
    
    return PolicyExplanation(
        overall_status=evaluation.status,
        total_rules=len(policy.rules),
        rules_evaluated=rules_evaluated,
        rules_matched=rules_matched,
        rules=traces
    )


def _build_violation_lookup(evaluation: PolicyEvaluationResult) -> Dict[str, List[str]]:
    """
    Build lookup map of rule_id → list of matched diff item keys.
    
    Args:
        evaluation: Policy evaluation result
    
    Returns:
        Dictionary mapping rule IDs to matched change keys
    """
    lookup = {}
    
    for violation in evaluation.violations:
        if violation.rule_id not in lookup:
            lookup[violation.rule_id] = []
        lookup[violation.rule_id].append(violation.diff_item.key)
    
    return lookup


def _trace_rule(
    rule: PolicyRule,
    diff: OnboardAIDiffReport,
    violations_by_rule: Dict[str, List[str]]
) -> RuleEvaluationTrace:
    """
    Generate trace for a single rule.
    
    Explains:
    - Was the rule evaluated?
    - Did it match?
    - Why or why not?
    
    Args:
        rule: Rule to trace
        diff: Diff report
        violations_by_rule: Lookup of rule violations
    
    Returns:
        RuleEvaluationTrace with explanation
    """
    
    # Check if rule was evaluated (enabled)
    if not rule.enabled:
        return RuleEvaluationTrace(
            rule_id=rule.id,
            description=rule.description,
            evaluated=False,
            matched=False,
            action=None,
            matched_changes=[],
            reason="This rule is disabled in the policy file."
        )
    
    # Check if rule matched (has violations)
    matched_changes = violations_by_rule.get(rule.id, [])
    matched = len(matched_changes) > 0
    
    if matched:
        # Rule matched - explain what triggered it
        reason = _explain_match(rule, diff, matched_changes)
        return RuleEvaluationTrace(
            rule_id=rule.id,
            description=rule.description,
            evaluated=True,
            matched=True,
            action=rule.action,
            matched_changes=matched_changes,
            reason=reason
        )
    else:
        # Rule did not match - explain why
        reason = _explain_no_match(rule, diff)
        return RuleEvaluationTrace(
            rule_id=rule.id,
            description=rule.description,
            evaluated=True,
            matched=False,
            action=None,
            matched_changes=[],
            reason=reason
        )


def _explain_match(
    rule: PolicyRule,
    diff: OnboardAIDiffReport,
    matched_changes: List[str]
) -> str:
    """
    Explain why a rule matched.
    
    Uses deterministic templates based on rule conditions.
    Same rule + same changes = same explanation text (always).
    
    Args:
        rule: Rule that matched
        diff: Diff report
        matched_changes: Keys of changes that matched
    
    Returns:
        Plain-English explanation (deterministic)
    """
    condition = rule.when
    
    # Build explanation based on conditions
    parts = []
    
    # Section condition
    if condition.section:
        parts.append(f"in the '{condition.section}' section")
    
    # Field condition (for checks)
    if condition.field:
        parts.append(f"where the '{condition.field}' field")
    
    # Change type condition
    if condition.change_type:
        if condition.change_type == "added":
            parts.append("was added")
        elif condition.change_type == "removed":
            parts.append("was removed")
        elif condition.change_type == "changed":
            parts.append("changed")
    
    # Value conditions
    if condition.from_values and condition.to_values:
        from_str = " or ".join(condition.from_values)
        to_str = " or ".join(condition.to_values)
        parts.append(f"from [{from_str}] to [{to_str}]")
    elif condition.to_values:
        to_str = " or ".join(condition.to_values)
        parts.append(f"to [{to_str}]")
    elif condition.from_values:
        from_str = " or ".join(condition.from_values)
        parts.append(f"from [{from_str}]")
    
    # Combine parts
    if parts:
        explanation = "This rule matched because changes were detected " + " ".join(parts) + "."
    else:
        explanation = "This rule matched based on the specified conditions."
    
    # Add matched changes
    if len(matched_changes) == 1:
        explanation += f"\n  Triggered by: {matched_changes[0]}"
    else:
        explanation += "\n  Triggered by:"
        for change_key in matched_changes:
            explanation += f"\n    - {change_key}"
    
    return explanation


def _explain_no_match(
    rule: PolicyRule,
    diff: OnboardAIDiffReport
) -> str:
    """
    Explain why a rule did not match.
    
    Uses deterministic analysis of what prevented the match.
    Same rule + same diff = same explanation text (always).
    
    Args:
        rule: Rule that didn't match
        diff: Diff report
    
    Returns:
        Plain-English explanation (deterministic)
    """
    condition = rule.when
    
    # Check what prevented the match
    
    # No changes at all
    if len(diff.changes) == 0:
        return "This rule was evaluated but did not match because no changes were detected."
    
    # No changes in specified section
    if condition.section:
        section_changes = [c for c in diff.changes if c.section == condition.section]
        if not section_changes:
            return f"This rule was evaluated but did not match because no changes were detected in the '{condition.section}' section."
    
    # No matching change type
    if condition.change_type:
        type_str = condition.change_type
        if condition.section:
            return f"This rule was evaluated but did not match because no '{type_str}' changes were detected in the '{condition.section}' section."
        else:
            return f"This rule was evaluated but did not match because no '{type_str}' changes were detected."
    
    # No matching values
    if condition.to_values:
        to_str = " or ".join(condition.to_values)
        if condition.field:
            return f"This rule was evaluated but did not match because no '{condition.field}' field changed to [{to_str}]."
        else:
            return f"This rule was evaluated but did not match because no changes resulted in [{to_str}]."
    
    # Generic no match
    return "This rule was evaluated but did not match the detected changes."


# =========================================================================
# Export Functions
# =========================================================================

def export_explanation_json(explanation: PolicyExplanation, output_path) -> None:
    """
    Export policy explanation as JSON.
    
    Args:
        explanation: Policy explanation to export
        output_path: Path to write JSON file
    """
    import json
    
    # Serialize with proper handling
    explanation_dict = explanation.model_dump(mode='json')
    
    # Write with stable key ordering
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(explanation_dict, f, indent=2, sort_keys=True, ensure_ascii=False)


def export_explanation_markdown(explanation: PolicyExplanation, output_path) -> None:
    """
    Export policy explanation as Markdown.
    
    Args:
        explanation: Policy explanation to export
        output_path: Path to write Markdown file
    """
    lines = []
    
    # Header
    lines.append("# Policy Explanation")
    lines.append("")
    lines.append(f"**Overall Status:** {explanation.overall_status}")
    lines.append(f"**Total Rules:** {explanation.total_rules}")
    lines.append(f"**Rules Evaluated:** {explanation.rules_evaluated}")
    lines.append(f"**Rules Matched:** {explanation.rules_matched}")
    lines.append("")
    
    # Rule traces
    lines.append("## Rule Evaluation Traces")
    lines.append("")
    
    for trace in explanation.rules:
        # Rule header
        lines.append(f"### {trace.rule_id}")
        lines.append("")
        lines.append(f"**Description:** {trace.description}")
        lines.append("")
        
        # Status
        if not trace.evaluated:
            lines.append("**Status:** ⏭ SKIPPED (disabled)")
        elif trace.matched:
            action_symbol = "❌" if trace.action == "FAIL" else "⚠️"
            lines.append(f"**Status:** {action_symbol} MATCHED ({trace.action})")
        else:
            lines.append("**Status:** ✓ NOT MATCHED")
        lines.append("")
        
        # Reason
        lines.append("**Reason:**")
        lines.append("")
        # Indent reason text
        for reason_line in trace.reason.split('\n'):
            lines.append(f"  {reason_line}")
        lines.append("")
        
        # Matched changes (if any)
        if trace.matched_changes:
            lines.append("**Matched Changes:**")
            lines.append("")
            for change in trace.matched_changes:
                lines.append(f"- `{change}`")
            lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

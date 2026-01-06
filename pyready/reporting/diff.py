"""
Deterministic report diff engine.

Compares two PyReady reports and produces a structured list of changes.
No interpretation, no scoring, no heuristics - pure comparison only.
"""

from datetime import datetime, timezone
from typing import List, Set

from pyready.schemas.report_schema import OnboardAIReport
from pyready.schemas.diff_schema import DiffItem, OnboardAIDiffReport


def diff_reports(
    old: OnboardAIReport,
    new: OnboardAIReport
) -> OnboardAIDiffReport:
    """
    Generate a deterministic diff between two reports.
    
    Args:
        old: Earlier report
        new: Later report
    
    Returns:
        OnboardAIDiffReport with all detected changes
    """
    changes = []
    
    # Diff each section in stable order
    changes.extend(_diff_capabilities(old, new))
    changes.extend(_diff_intent(old, new))
    changes.extend(_diff_checks(old, new))
    changes.extend(_diff_recommendations(old, new))
    changes.extend(_diff_run_command(old, new))
    
    return OnboardAIDiffReport(
        from_report=old.generated_at.isoformat(),
        to_report=new.generated_at.isoformat(),
        generated_at=datetime.now(timezone.utc),
        changes=changes
    )


# =========================================================================
# Capabilities Diff
# =========================================================================

def _diff_capabilities(old: OnboardAIReport, new: OnboardAIReport) -> List[DiffItem]:
    """Diff capability changes"""
    changes = []
    
    old_caps = old.capabilities
    new_caps = new.capabilities
    
    # Check each capability field
    capability_fields = [
        'has_python_files',
        'has_dependency_declaration',
        'has_isolated_environment',
        'has_reproducible_environment',
        'has_detectable_entrypoint'
    ]
    
    for field in capability_fields:
        old_val = getattr(old_caps, field)
        new_val = getattr(new_caps, field)
        
        if old_val != new_val:
            # Capability gained or lost
            if not old_val and new_val:
                changes.append(DiffItem(
                    section="capabilities",
                    key=field,
                    change_type="added",
                    before=None,
                    after=f"{field} is now detected"
                ))
            elif old_val and not new_val:
                changes.append(DiffItem(
                    section="capabilities",
                    key=field,
                    change_type="removed",
                    before=f"{field} was detected",
                    after=None
                ))
    
    # Check evidence changes (only for capabilities that exist in both)
    for field in capability_fields:
        if getattr(old_caps, field) and getattr(new_caps, field):
            old_evidence = set(old_caps.evidence.get(field, []))
            new_evidence = set(new_caps.evidence.get(field, []))
            
            if old_evidence != new_evidence:
                added = new_evidence - old_evidence
                removed = old_evidence - new_evidence
                
                if added or removed:
                    changes.append(DiffItem(
                        section="capabilities",
                        key=f"{field}_evidence",
                        change_type="changed",
                        before=f"{len(old_evidence)} evidence items",
                        after=f"{len(new_evidence)} evidence items"
                    ))
    
    return changes


# =========================================================================
# Intent Diff
# =========================================================================

def _diff_intent(old: OnboardAIReport, new: OnboardAIReport) -> List[DiffItem]:
    """Diff project intent changes"""
    changes = []
    
    if old.project_intent != new.project_intent:
        changes.append(DiffItem(
            section="intent",
            key="project_intent",
            change_type="changed",
            before=old.project_intent.upper(),
            after=new.project_intent.upper()
        ))
    
    return changes


# =========================================================================
# Checks Diff
# =========================================================================

def _diff_checks(old: OnboardAIReport, new: OnboardAIReport) -> List[DiffItem]:
    """Diff environment check changes"""
    changes = []
    
    # Create maps by category
    old_checks = {check.category: check for check in old.checks}
    new_checks = {check.category: check for check in new.checks}
    
    # Find all categories (union)
    all_categories = set(old_checks.keys()) | set(new_checks.keys())
    
    for category in sorted(all_categories):  # Stable ordering
        old_check = old_checks.get(category)
        new_check = new_checks.get(category)
        
        if old_check is None:
            # Check added
            changes.append(DiffItem(
                section="checks",
                key=category,
                change_type="added",
                before=None,
                after=f"Status: {new_check.status}"
            ))
        
        elif new_check is None:
            # Check removed
            changes.append(DiffItem(
                section="checks",
                key=category,
                change_type="removed",
                before=f"Status: {old_check.status}",
                after=None
            ))
        
        else:
            # Check exists in both - compare fields
            
            # Status change
            if old_check.status != new_check.status:
                changes.append(DiffItem(
                    section="checks",
                    key=f"{category}_status",
                    change_type="changed",
                    before=old_check.status,
                    after=new_check.status
                ))
            
            # Message change
            if old_check.message != new_check.message:
                changes.append(DiffItem(
                    section="checks",
                    key=f"{category}_message",
                    change_type="changed",
                    before=old_check.message,
                    after=new_check.message
                ))
            
            # Details change
            if old_check.details != new_check.details:
                changes.append(DiffItem(
                    section="checks",
                    key=f"{category}_details",
                    change_type="changed",
                    before=str(old_check.details) if old_check.details else None,
                    after=str(new_check.details) if new_check.details else None
                ))
            
            # Fix command change
            if old_check.fix_command != new_check.fix_command:
                changes.append(DiffItem(
                    section="checks",
                    key=f"{category}_fix_command",
                    change_type="changed",
                    before=old_check.fix_command,
                    after=new_check.fix_command
                ))
    
    return changes


# =========================================================================
# Recommendations Diff
# =========================================================================

def _diff_recommendations(old: OnboardAIReport, new: OnboardAIReport) -> List[DiffItem]:
    """Diff recommendation changes"""
    changes = []
    
    # Create maps by title
    old_recs = {rec.title: rec for rec in old.recommendations}
    new_recs = {rec.title: rec for rec in new.recommendations}
    
    # Find all titles (union)
    all_titles = set(old_recs.keys()) | set(new_recs.keys())
    
    for title in sorted(all_titles):  # Stable ordering
        old_rec = old_recs.get(title)
        new_rec = new_recs.get(title)
        
        if old_rec is None:
            # Recommendation added
            changes.append(DiffItem(
                section="recommendations",
                key=title,
                change_type="added",
                before=None,
                after=title
            ))
        
        elif new_rec is None:
            # Recommendation removed
            changes.append(DiffItem(
                section="recommendations",
                key=title,
                change_type="removed",
                before=title,
                after=None
            ))
        
        else:
            # Recommendation exists in both - check if evidence changed
            old_evidence = set(old_rec.evidence)
            new_evidence = set(new_rec.evidence)
            
            if old_evidence != new_evidence:
                changes.append(DiffItem(
                    section="recommendations",
                    key=f"{title}_evidence",
                    change_type="changed",
                    before=f"{len(old_evidence)} evidence items",
                    after=f"{len(new_evidence)} evidence items"
                ))
            
            # Check if description changed
            if old_rec.description != new_rec.description:
                changes.append(DiffItem(
                    section="recommendations",
                    key=f"{title}_description",
                    change_type="changed",
                    before="description changed",
                    after="description changed"
                ))
    
    return changes


# =========================================================================
# Run Command Diff
# =========================================================================

def _diff_run_command(old: OnboardAIReport, new: OnboardAIReport) -> List[DiffItem]:
    """Diff run command changes"""
    changes = []
    
    # Command change
    if old.run_command != new.run_command:
        changes.append(DiffItem(
            section="run_command",
            key="command",
            change_type="changed",
            before=old.run_command,
            after=new.run_command
        ))
    
    # Evidence change
    old_evidence = set(old.run_command_evidence or [])
    new_evidence = set(new.run_command_evidence or [])
    
    if old_evidence != new_evidence:
        changes.append(DiffItem(
            section="run_command",
            key="evidence",
            change_type="changed",
            before=f"{len(old_evidence)} evidence items",
            after=f"{len(new_evidence)} evidence items"
        ))
    
    return changes

# =========================================================================
# Export Functions
# =========================================================================

def export_diff_json(diff: OnboardAIDiffReport, output_path) -> None:
    """
    Export diff as JSON.
    
    Args:
        diff: Diff report to export
        output_path: Path to write JSON file
    """
    import json
    from pathlib import Path
    
    # Serialize with proper handling
    diff_dict = diff.model_dump(mode='json')
    
    # Write with stable key ordering
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(diff_dict, f, indent=2, sort_keys=True, ensure_ascii=False)


def export_diff_markdown(diff: OnboardAIDiffReport, output_path) -> None:
    """
    Export diff as Markdown.
    
    Args:
        diff: Diff report to export
        output_path: Path to write Markdown file
    """
    from pathlib import Path
    
    lines = []
    
    # Header
    lines.append("# pyready diff Report")
    lines.append("")
    lines.append(f"**From:** {diff.from_report}")
    lines.append(f"**To:** {diff.to_report}")
    lines.append(f"**Generated:** {diff.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append("")
    
    if not diff.changes:
        lines.append("**No changes detected** - reports are identical.")
        lines.append("")
    else:
        lines.append(f"**Total Changes:** {len(diff.changes)}")
        lines.append("")
        
        # Group changes by section
        sections = {}
        for change in diff.changes:
            if change.section not in sections:
                sections[change.section] = []
            sections[change.section].append(change)
        
        # Display each section
        section_titles = {
            'capabilities': 'Capability Changes',
            'intent': 'Intent Changes',
            'checks': 'Environment Check Changes',
            'recommendations': 'Recommendation Changes',
            'run_command': 'Run Command Changes'
        }
        
        for section_key in ['capabilities', 'intent', 'checks', 'recommendations', 'run_command']:
            if section_key in sections:
                lines.append(f"## {section_titles[section_key]}")
                lines.append("")
                
                for change in sections[section_key]:
                    change_symbol = _get_change_symbol(change.change_type)
                    lines.append(f"### {change_symbol} {change.key}")
                    lines.append("")
                    lines.append(f"**Type:** {change.change_type}")
                    lines.append("")
                    
                    if change.before:
                        lines.append(f"**Before:** {change.before}")
                        lines.append("")
                    
                    if change.after:
                        lines.append(f"**After:** {change.after}")
                        lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _get_change_symbol(change_type: str) -> str:
    """Get symbol for change type"""
    if change_type == "added":
        return "+"
    elif change_type == "removed":
        return "-"
    elif change_type == "changed":
        return "~"
    else:
        return "○"

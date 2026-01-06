"""
Deterministic report generator.

This module accepts already-computed results and serializes them
into machine-readable formats. No additional computation is performed.
"""

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from pyready.schemas.report_schema import OnboardAIReport
from pyready.schemas.capability_schema import ProjectCapabilities
from pyready.schemas.env_schema import CheckResult, CheckStatus
from pyready.recommendations.models import Recommendation
from pyready.project_intent.models import ProjectIntent


# OnboardAI version (update this when releasing new versions)
ONBOARDAI_VERSION = "0.1.0"


def generate_report(
    *,
    project_path: str,
    project_type: str,
    intent: ProjectIntent,
    capabilities: ProjectCapabilities,
    checks: List[CheckResult],
    recommendations: List[Recommendation],
    run_command: Optional[str],
    run_command_evidence: Optional[List[str]],
) -> OnboardAIReport:
    """
    Generate a complete PyReady report from already-computed results.
    
    This function is pure serialization — no additional computation,
    no filesystem access, no logic beyond composition.
    
    Args:
        project_path: Path to the checked project
        project_type: Detected project type
        intent: Classified project intent
        capabilities: Detected capabilities
        checks: Environment check results
        recommendations: Generated recommendations
        run_command: Detected run command (optional)
        run_command_evidence: Evidence for run command (optional)
    
    Returns:
        OnboardAIReport with all data serialized
    """
    return OnboardAIReport(
        tool_version=ONBOARDAI_VERSION,
        generated_at=datetime.now(timezone.utc),
        project_path=str(Path(project_path).resolve()),
        project_type=project_type,
        project_intent=intent.value,
        capabilities=capabilities,
        checks=checks,
        recommendations=recommendations,
        run_command=run_command,
        run_command_evidence=run_command_evidence
    )


def export_json(report: OnboardAIReport, output_path: Path) -> None:
    """
    Export report as JSON.
    
    Args:
        report: PyReady report to export
        output_path: Path to write JSON file
    """
    # Use model_dump() with mode='json' to handle enums properly
    report_dict = report.model_dump(mode='json')
    
    # Write with stable key ordering and pretty formatting
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report_dict, f, indent=2, sort_keys=True, ensure_ascii=False)



def export_markdown(report: OnboardAIReport, output_path: Path) -> None:
    """
    Export report as Markdown.
    
    Args:
        report: PyReady report to export
        output_path: Path to write Markdown file
    """
    lines = []
    
    # Header
    lines.append("# PyReady report")
    lines.append("")
    lines.append(f"**Generated:** {report.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
    lines.append(f"**Tool Version:** {report.tool_version}")
    lines.append("")
    
    # Project Overview
    lines.append("## Project Overview")
    lines.append("")
    lines.append(f"- **Path:** `{report.project_path}`")
    lines.append(f"- **Type:** {report.project_type}")
    lines.append(f"- **Intent:** {report.project_intent.upper()}")
    lines.append("")
    
    # Capabilities
    lines.append("## Capabilities")
    lines.append("")
    
    capability_labels = {
        'has_python_files': 'Python files detected',
        'has_dependency_declaration': 'Dependency declaration found',
        'has_isolated_environment': 'Isolated environment (venv)',
        'has_reproducible_environment': 'Reproducible environment (lock file)',
        'has_detectable_entrypoint': 'Entry point detectable',
    }
    
    for field_name, label in capability_labels.items():
        has_capability = getattr(report.capabilities, field_name)
        status = "✓" if has_capability else "○"
        lines.append(f"- {status} {label}")
        
        # Show evidence if available
        if has_capability and field_name in report.capabilities.evidence:
            evidence_items = report.capabilities.evidence[field_name]
            for item in evidence_items[:3]:  # Limit to first 3
                lines.append(f"  - `{item}`")
            if len(evidence_items) > 3:
                lines.append(f"  - *... and {len(evidence_items) - 3} more*")
    
    lines.append("")
    
    # Environment Checks
    lines.append("## Environment Checks")
    lines.append("")
    
    for check in report.checks:
        status_symbol = _get_markdown_status_symbol(check.status)
        lines.append(f"### {status_symbol} {check.category}")
        lines.append("")
        lines.append(f"**Status:** {check.status.value.upper()}")
        lines.append("")
        lines.append(f"**Message:** {check.message}")
        lines.append("")
        
        if check.details:
            lines.append(f"**Details:** {check.details}")
            lines.append("")
        
        if check.fix_command:
            lines.append(f"**Suggested Fix:** `{check.fix_command}`")
            lines.append("")
    
    # Summary
    passed = sum(1 for c in report.checks if c.status == CheckStatus.PASS)
    failed = sum(1 for c in report.checks if c.status == CheckStatus.FAIL)
    warnings = sum(1 for c in report.checks if c.status == CheckStatus.WARN)
    
    lines.append("### Summary")
    lines.append("")
    lines.append(f"- Total checks: {len(report.checks)}")
    lines.append(f"- Passed: {passed}")
    lines.append(f"- Failed: {failed}")
    lines.append(f"- Warnings: {warnings}")
    lines.append("")
    
    # Recommendations
    lines.append("## Recommendations")
    lines.append("")
    
    if not report.recommendations:
        if report.project_intent == 'script':
            lines.append("*No recommendations — scripts don't require complex setup.*")
        else:
            lines.append("*No recommendations — project structure looks healthy.*")
        lines.append("")
    else:
        for rec in report.recommendations:
            lines.append(f"### {rec.title}")
            lines.append("")
            lines.append(rec.description)
            lines.append("")
            
            lines.append("**Evidence:**")
            lines.append("")
            for evidence_item in rec.evidence:
                lines.append(f"- {evidence_item}")
            lines.append("")
            
            if rec.example_command:
                lines.append(f"**Example:** `{rec.example_command}`")
                lines.append("")
    
    # Run Command
    lines.append("## Run Command")
    lines.append("")
    
    if report.run_command:
        lines.append(f"**Command:** `{report.run_command}`")
        lines.append("")
        
        if report.run_command_evidence:
            lines.append("**Evidence:**")
            lines.append("")
            for evidence_item in report.run_command_evidence:
                lines.append(f"- {evidence_item}")
            lines.append("")
    else:
        lines.append("*No safe run command detected.*")
        lines.append("")
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def _get_markdown_status_symbol(status: CheckStatus) -> str:
    """Get symbol for check status in Markdown"""
    if status == CheckStatus.PASS:
        return "✓"
    elif status == CheckStatus.FAIL:
        return "✗"
    elif status == CheckStatus.WARN:
        return "⚠"
    elif status == CheckStatus.INFO:
        return "ℹ"
    else:
        return "○"

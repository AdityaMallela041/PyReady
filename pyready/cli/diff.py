"""Diff command implementation"""

import json
from pathlib import Path
from rich.console import Console

from pyready.schemas.report_schema import OnboardAIReport
from pyready.reporting import diff_reports, export_diff_json, export_diff_markdown
from pyready.policy import (
    load_policy, 
    evaluate_policy, 
    explain_policy,
    export_explanation_json,
    export_explanation_markdown
)

console = Console()


def diff_command(
    old_path: Path, 
    new_path: Path, 
    output_path: Path = None,
    policy_path: Path = None,
    explain_policy_flag: bool = False
) -> int:
    """
    Compare two PyReady reports and show what changed.
    
    Args:
        old_path: Path to older report JSON
        new_path: Path to newer report JSON
        output_path: Optional path to export diff report
        policy_path: Optional path to policy file for evaluation
        explain_policy_flag: Whether to show policy explanation
    
    Returns:
        Exit code: 0 (PASS), 1 (WARN), 2 (FAIL)
    """
    
    # Load reports
    try:
        with open(old_path, 'r', encoding='utf-8') as f:
            old_data = json.load(f)
        old_report = OnboardAIReport(**old_data)
    except Exception as e:
        console.print(f"[red]Error loading old report:[/red] {e}")
        return 2
    
    try:
        with open(new_path, 'r', encoding='utf-8') as f:
            new_data = json.load(f)
        new_report = OnboardAIReport(**new_data)
    except Exception as e:
        console.print(f"[red]Error loading new report:[/red] {e}")
        return 2
    
    # Generate diff
    diff = diff_reports(old_report, new_report)
    
    # Display summary
    _display_diff_summary(diff)
    
    # Export if requested
    if output_path:
        try:
            suffix = output_path.suffix.lower()
            if suffix == '.json':
                export_diff_json(diff, output_path)
                console.print(f"\n✓ [green]Diff exported to:[/green] {output_path}")
            elif suffix == '.md':
                export_diff_markdown(diff, output_path)
                console.print(f"\n✓ [green]Diff exported to:[/green] {output_path}")
            else:
                console.print(f"\n[yellow]⚠ Unsupported format:[/yellow] {suffix}")
                console.print("  Supported formats: .json, .md")
        except Exception as e:
            console.print(f"\n[red]Error exporting diff:[/red] {e}")
    
    # Evaluate policy if provided
    exit_code = 0
    if policy_path:
        try:
            policy = load_policy(policy_path)
            result = evaluate_policy(diff, policy)
            
            console.print()  # Blank line
            _display_policy_result(result)
            
            # Generate explanation if requested
            if explain_policy_flag:
                explanation = explain_policy(diff, policy, result)
                console.print()  # Blank line
                _display_policy_explanation(explanation)
            
            # Set exit code based on policy result
            if result.status == "FAIL":
                exit_code = 2
            elif result.status == "WARN":
                exit_code = 1
            else:
                exit_code = 0
        
        except FileNotFoundError as e:
            console.print(f"\n[red]Policy file not found:[/red] {e}")
            exit_code = 2
        except Exception as e:
            console.print(f"\n[red]Error evaluating policy:[/red] {e}")
            exit_code = 2
    
    return exit_code


def _display_diff_summary(diff) -> None:
    """Display human-readable diff summary"""
    
    console.print(f"\n📊 [bold]Diff Summary[/bold]")
    console.print(f"From: [cyan]{diff.from_report}[/cyan]")
    console.print(f"To:   [cyan]{diff.to_report}[/cyan]")
    console.print()
    
    if not diff.changes:
        console.print("✓ [green]No changes detected[/green] - reports are identical.")
        return
    
    console.print(f"Total changes: [yellow]{len(diff.changes)}[/yellow]\n")
    
    # Group by section
    sections = {}
    for change in diff.changes:
        if change.section not in sections:
            sections[change.section] = []
        sections[change.section].append(change)
    
    # Display by section
    section_titles = {
        'capabilities': '📦 Capability Changes',
        'intent': '🎯 Intent Changes',
        'checks': '✓ Check Changes',
        'recommendations': '💡 Recommendation Changes',
        'run_command': '▶ Run Command Changes'
    }
    
    for section_key in ['capabilities', 'intent', 'checks', 'recommendations', 'run_command']:
        if section_key in sections:
            console.print(f"[bold]{section_titles[section_key]}[/bold]")
            
            for change in sections[section_key]:
                symbol = _get_change_symbol_colored(change.change_type)
                console.print(f"  {symbol} {change.key}")
                
                if change.before:
                    console.print(f"    [dim]Before: {change.before}[/dim]")
                if change.after:
                    console.print(f"    [dim]After:  {change.after}[/dim]")
            
            console.print()


def _display_policy_result(result) -> None:
    """Display policy evaluation result"""
    
    # Header with status
    if result.status == "PASS":
        console.print("🟢 [bold green]Policy Evaluation: PASS[/bold green]")
        console.print(f"  {result.rules_evaluated} rules evaluated, {result.changes_checked} changes checked")
        console.print("  No violations detected")
    
    elif result.status == "WARN":
        console.print("🟡 [bold yellow]Policy Evaluation: WARN[/bold yellow]")
        console.print(f"  {result.rules_evaluated} rules evaluated, {result.changes_checked} changes checked")
        console.print(f"  {len(result.violations)} warning(s) detected\n")
        
        _display_violations(result.violations)
    
    elif result.status == "FAIL":
        console.print("🛑 [bold red]Policy Evaluation: FAIL[/bold red]")
        console.print(f"  {result.rules_evaluated} rules evaluated, {result.changes_checked} changes checked")
        console.print(f"  {len(result.violations)} violation(s) detected\n")
        
        _display_violations(result.violations)


def _display_violations(violations) -> None:
    """Display policy violations"""
    
    console.print("[bold]Violations:[/bold]\n")
    
    for violation in violations:
        # Symbol based on action
        symbol = "✖" if violation.action == "FAIL" else "⚠"
        color = "red" if violation.action == "FAIL" else "yellow"
        
        console.print(f"  [{color}]{symbol} {violation.rule_id}[/{color}]")
        console.print(f"    {violation.rule_description}")
        console.print(f"    Change: [cyan]{violation.diff_item.key}[/cyan]")
        
        if violation.diff_item.before:
            console.print(f"    Before: [dim]{violation.diff_item.before}[/dim]")
        if violation.diff_item.after:
            console.print(f"    After:  [dim]{violation.diff_item.after}[/dim]")
        
        console.print()


def _display_policy_explanation(explanation) -> None:
    """Display policy explanation"""
    
    console.print("📖 [bold]Policy Explanation[/bold]")
    console.print(f"  {explanation.rules_matched} of {explanation.rules_evaluated} rules matched")
    console.print()
    
    for trace in explanation.rules:
        # Rule ID
        console.print(f"[bold]Rule: {trace.rule_id}[/bold]")
        
        # Status with symbol
        if not trace.evaluated:
            console.print("  Status: [dim]⏭ SKIPPED (disabled)[/dim]")
        elif trace.matched:
            if trace.action == "FAIL":
                console.print(f"  Status: [red]❌ MATCHED ({trace.action})[/red]")
            else:
                console.print(f"  Status: [yellow]⚠️  MATCHED ({trace.action})[/yellow]")
        else:
            console.print("  Status: [green]✓ NOT MATCHED[/green]")
        
        # Reason
        console.print("  Reason:")
        for line in trace.reason.split('\n'):
            if line.strip():
                console.print(f"    [dim]{line}[/dim]")
        
        console.print()


def _get_change_symbol_colored(change_type: str) -> str:
    """Get colored symbol for change type"""
    if change_type == "added":
        return "[green]+[/green]"
    elif change_type == "removed":
        return "[red]-[/red]"
    elif change_type == "changed":
        return "[yellow]~[/yellow]"
    else:
        return "○"

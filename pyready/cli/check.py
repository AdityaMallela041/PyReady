"""Check command implementation"""

import sys
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.panel import Panel

from pyready.project_detection import ProjectType
from pyready.project_detection.capabilities import CapabilityDetector
from pyready.schemas.capability_schema import CapabilityCheckResult
from pyready.project_intent import classify_project_intent
from pyready.recommendations import generate_recommendations
from pyready.reporting import generate_report, export_json, export_markdown
from pyready.env_checker import EnvironmentChecker
from pyready.schemas.env_schema import CheckStatus, CheckResult

# Import run detection (will fail gracefully if backend not available)
try:
    from pyready.run_detection.detector import RunCommandDetector
    RUN_DETECTION_AVAILABLE = True
except ImportError:
    RUN_DETECTION_AVAILABLE = False

# Import explanation generator
try:
    from pyready.explanation.generator import ExplanationGenerator
    EXPLANATION_AVAILABLE = True
except ImportError:
    EXPLANATION_AVAILABLE = False

console = Console()


def check_environment(
    project_path: Path,
    project_type: ProjectType,
    enable_explanations: bool = False,
    output_path: Optional[Path] = None
) -> None:
    """
    Check the development environment for a project.
    
    Args:
        project_path: Path to the project directory
        project_type: Detected project type
        enable_explanations: Whether to include AI-assisted explanations (requires GROQ_API_KEY)
        output_path: Optional path to export report (infers format from extension)
    """
    console.print(f"🔍 Checking environment for: [cyan]{project_path}[/cyan]\n")
    
    # Detect and display project capabilities
    capabilities = None
    intent = None
    
    try:
        capability_detector = CapabilityDetector(project_path)
        capability_result = capability_detector.detect()
        capabilities = capability_result.capabilities
        
        _display_capabilities(capability_result)
        
        # Display project intent
        intent, _ = classify_project_intent(capabilities, project_path)
        _display_intent(capabilities, project_path)
    
    except Exception as e:
        console.print(f"[yellow]⚠ Could not detect capabilities:[/yellow] {str(e)}\n")
    
    # Run environment checks via orchestrator
    report = None
    try:
        checker = EnvironmentChecker(str(project_path), project_type=project_type.value)
        report = checker.run_checks()
        
        # Display results
        _display_check_results(report)
    
    except Exception as e:
        console.print(f"[red]Error running environment checks:[/red] {str(e)}\n")
        return
    
    # Generate recommendations
    recommendations = []
    if capabilities and intent and report:
        try:
            recommendations = generate_recommendations(capabilities, intent, report.checks)
            _display_recommendations(capabilities, intent, report.checks)
        except Exception as e:
            console.print(f"[yellow]⚠ Could not generate recommendations:[/yellow] {str(e)}\n")
    
    # Run command detection (for export only - don't display yet)
    run_cmd = None
    run_cmd_evidence = None
    
    if RUN_DETECTION_AVAILABLE:
        try:
            detector = RunCommandDetector(project_path, project_type=project_type.value)
            result = detector.detect()
            
            if result.has_command():
                run_cmd = result.command
                # Convert evidence to list of strings (evidence items may be objects)
                run_cmd_evidence = [str(e) for e in result.evidence] if result.evidence else None
        
        except Exception:
            pass
    
    # Display run command (separate from export data collection)
    detect_run_command(project_path, project_type, enable_explanations)
    
    # Export report if output path is provided
    if output_path and capabilities and intent and report:
        try:
            _export_report(
                project_path=project_path,
                project_type=project_type.value,
                intent=intent,
                capabilities=capabilities,
                checks=report.checks,
                recommendations=recommendations,
                run_command=run_cmd,
                run_command_evidence=run_cmd_evidence,
                output_path=output_path
            )
        except Exception as e:
            console.print(f"\n[red]Error exporting report:[/red] {str(e)}")


def _display_capabilities(result: CapabilityCheckResult) -> None:
    """Display project capabilities"""
    console.print("📦 [bold]Project capabilities:[/bold]")
    
    caps = result.capabilities
    
    # Define display order and labels
    capability_display = [
        ('has_python_files', 'Python files detected'),
        ('has_dependency_declaration', 'Dependency declaration found'),
        ('has_isolated_environment', 'Isolated environment (venv)'),
        ('has_reproducible_environment', 'Reproducible environment (lock file)'),
        ('has_detectable_entrypoint', 'Entry point detectable'),
    ]
    
    for field_name, label in capability_display:
        has_capability = getattr(caps, field_name)
        
        if has_capability:
            symbol = "✔"
            color = "green"
            status = label
        else:
            symbol = "○"
            color = "dim"
            status = f"{label}: not detected"
        
        console.print(f"  {symbol} [{color}]{status}[/{color}]")
        
        # Show evidence if available and capability is true
        if has_capability and field_name in caps.evidence:
            evidence_items = caps.evidence[field_name]
            
            # Show first 3 evidence items
            for item in evidence_items[:3]:
                console.print(f"    [dim]• {item}[/dim]")
            
            # Show count if more than 3
            if len(evidence_items) > 3:
                remaining = len(evidence_items) - 3
                console.print(f"    [dim]• ... and {remaining} more[/dim]")
    
    console.print()


def _display_intent(capabilities, project_path: Path) -> None:
    """Display project intent classification"""
    intent, reasoning = classify_project_intent(capabilities, project_path)
    
    # Icon mapping
    icons = {
        'script': '📄',
        'library': '📦',
        'application': '🚀',
        'service': '⚙️',
        'unknown': '❓'
    }
    
    icon = icons.get(intent.value, '❓')
    console.print(f"{icon} [bold]Project intent:[/bold] {intent}")
    console.print(f"  [dim]{reasoning}[/dim]")
    console.print()


def _display_check_results(report) -> None:
    """Display environment check results"""
    for check in report.checks:
        status_symbol = _get_status_symbol(check.status)
        status_color = _get_status_color(check.status)
        
        console.print(f"{status_symbol} [{status_color}]{check.category}:[/{status_color}] {check.message}")
        
        # Display details (improved formatting)
        if check.details:
            if isinstance(check.details, dict):
                # Extract and display info from dict
                info = check.details.get("info", "")
                if info:
                    console.print(f"  [dim]{info}[/dim]")
            else:
                console.print(f"  [dim]{check.details}[/dim]")
        
        if check.fix_command:
            console.print(f"  → [yellow]Suggested fix:[/yellow] {check.fix_command}\n")
    
    # Display summary
    console.print("─" * 80)
    console.print("\n📊 [bold]Summary:[/bold]")
    console.print(f"  Total checks: {report.summary['total']}")
    console.print(f"  ✔ [green]Passed:[/green] {report.summary['passed']}")
    console.print(f"  ✖ [red]Failed:[/red] {report.summary['failed']}")
    console.print(f"  ⚠ [yellow]Warnings:[/yellow] {report.summary['warnings']}")
    console.print()


def _display_recommendations(
    capabilities,
    intent,
    check_results: List[CheckResult]
) -> None:
    """Display recommendations for project improvement"""
    console.print("─" * 80)
    console.print("\n💡 [bold]Recommendations:[/bold]\n")
    
    recommendations = generate_recommendations(capabilities, intent, check_results)
    
    if not recommendations:
        # Special message for SCRIPT intent
        if intent.value == 'script':
            console.print("  [dim]No recommendations — scripts don't require complex setup.[/dim]")
        else:
            console.print("  [dim]No recommendations — project structure looks healthy.[/dim]")
        console.print()
        return
    
    for rec in recommendations:
        console.print(f"  [bold cyan]• {rec.title}[/bold cyan]")
        console.print(f"    {rec.description}")
        
        # Display evidence
        console.print(f"    [dim]Evidence:[/dim]")
        for evidence_item in rec.evidence:
            console.print(f"      [dim]- {evidence_item}[/dim]")
        
        # Display example command if present
        if rec.example_command:
            console.print(f"    [yellow]Example:[/yellow] {rec.example_command}")
        
        console.print()


def _export_report(
    project_path: Path,
    project_type: str,
    intent,
    capabilities,
    checks,
    recommendations,
    run_command,
    run_command_evidence,
    output_path: Path
) -> None:
    """Export report to specified format"""
    # Generate report
    report_obj = generate_report(
        project_path=str(project_path),
        project_type=project_type,
        intent=intent,
        capabilities=capabilities,
        checks=checks,
        recommendations=recommendations,
        run_command=run_command,
        run_command_evidence=run_command_evidence
    )
    
    # Determine format from extension
    suffix = output_path.suffix.lower()
    
    if suffix == '.json':
        export_json(report_obj, output_path)
        console.print(f"\n✓ [green]Report exported to:[/green] {output_path}")
    
    elif suffix == '.md':
        export_markdown(report_obj, output_path)
        console.print(f"\n✓ [green]Report exported to:[/green] {output_path}")
    
    else:
        console.print(f"\n[yellow]⚠ Unsupported format:[/yellow] {suffix}")
        console.print("  Supported formats: .json, .md")


def _get_status_symbol(status: CheckStatus) -> str:
    """Get symbol for check status"""
    if status == CheckStatus.PASS:
        return "✔"
    elif status == CheckStatus.FAIL:
        return "✖"
    elif status == CheckStatus.WARN:
        return "⚠"
    elif status == CheckStatus.INFO:
        return "ℹ"
    else:
        return "ℹ"


def _get_status_color(status: CheckStatus) -> str:
    """Get color for check status"""
    if status == CheckStatus.PASS:
        return "green"
    elif status == CheckStatus.FAIL:
        return "red"
    elif status == CheckStatus.WARN:
        return "yellow"
    elif status == CheckStatus.INFO:
        return "cyan"
    else:
        return "cyan"


def detect_run_command(project_path: Path, project_type: ProjectType, enable_explanations: bool = False) -> None:
    """
    Detect and display recommended run command for the project.
    
    Args:
        project_path: Path to the project directory
        project_type: Detected project type
        enable_explanations: Whether to generate AI explanations (requires GROQ_API_KEY)
    """
    if not RUN_DETECTION_AVAILABLE:
        console.print("─" * 80)
        console.print("\n⚠ [yellow]Run command detection unavailable[/yellow]")
        console.print("  [dim]Backend module not found[/dim]\n")
        return
    
    console.print("─" * 80)
    console.print("\n▶ [bold]Recommended run command:[/bold]\n")
    
    try:
        detector = RunCommandDetector(project_path, project_type=project_type.value)
        result = detector.detect()
        
        if result.has_command():
            # Display command
            console.print(f"  [cyan]{result.command}[/cyan]")
            console.print()
            
            # Display evidence
            console.print("  [dim]Evidence:[/dim]")
            for evidence_item in result.evidence:
                console.print(f"    • {evidence_item}")
            
            # Display detection basis
            basis_colors = {
                "explicit": "green",
                "pattern-based": "cyan",
                "fallback": "yellow",
                "none": "red"
            }
            
            basis_value = result.detection_basis.value
            color = basis_colors.get(basis_value, "white")
            console.print(f"\n  [dim]Detection basis:[/dim] [{color}]{basis_value}[/{color}]")
            
            # AI explanation (optional) - PHASE 14.5 HARDENING
            if enable_explanations:
                generate_explanation(result, project_path)
        
        else:
            console.print("  [yellow]No safe run command detected.[/yellow]")
            console.print()
            console.print("  [dim]Possible reasons:[/dim]")
            console.print("    • No Poetry scripts defined in pyproject.toml")
            console.print("    • No FastAPI/Flask app detected")
            console.print('    • No if __name__ == "__main__" entry point found')
            console.print()
            console.print("  [dim]Manual options:[/dim]")
            console.print("    • Add a script to pyproject.toml [tool.poetry.scripts]")
            console.print("    • Run specific module: python -m <module>")
            console.print("    • Check README for instructions")
            
            # AI explanation for "no command" case
            if enable_explanations:
                generate_explanation(result, project_path)
        
        console.print()
    
    except Exception as e:
        console.print(f"  [red]Error detecting run command:[/red] {str(e)}")
        console.print()


def generate_explanation(result, project_path: Path) -> None:
    """
    Generate and display LLM-generated explanation.
    
    This is the ONLY place in the check command where Groq/LLM is used.
    It is purely for human-readable explanation and does NOT affect:
    - Capability detection
    - Environment checks
    - Policy evaluation
    - Report exports
    - Exit codes
    
    Args:
        result: RunCommandResult from detection
        project_path: Path to the project directory
    """
    if not EXPLANATION_AVAILABLE:
        console.print("\n  [dim]ℹ️  Natural language explanations unavailable (backend module not found)[/dim]")
        return
    
    try:
        generator = ExplanationGenerator()
        
        # PHASE 14.5: Check if Groq is available before attempting
        if not generator.is_available():
            console.print("\n  [dim]ℹ️  Natural language explanations unavailable (GROQ_API_KEY not set)[/dim]")
            return
        
        console.print("\n  [dim]ℹ️  Generating explanation...[/dim]")
        
        # Get project name from path
        project_name = project_path.name
        
        # Generate explanation from deterministic context only
        explanation = generator.explain_run_command(result, project_name)
        
        if explanation:
            console.print(f"\n  [bold cyan]ℹ️  Explanation (AI-assisted):[/bold cyan]")
            
            # Indent explanation text
            for line in explanation.split("\n"):
                if line.strip():
                    console.print(f"    {line}")
        else:
            # PHASE 14.5: Silent fallback if Groq fails
            console.print("\n  [dim]ℹ️  Natural language explanation unavailable[/dim]")
    
    except Exception as e:
        # PHASE 14.5: LLM errors should never break the CLI
        # Silent fallback with optional user-friendly message
        error_msg = str(e)
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            console.print(f"\n  [dim]ℹ️  Natural language explanation timed out[/dim]")
        else:
            # Silent fallback for other errors
            console.print(f"\n  [dim]ℹ️  Natural language explanation unavailable[/dim]")

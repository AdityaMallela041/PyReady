"""PyReady CLI - Project environment checker and assistant"""

# PHASE 14.5: Load environment variables from .env file
# This must be at the very top, before any other imports
from dotenv import load_dotenv
load_dotenv()

import typer
from pathlib import Path
from rich.console import Console

from pyready.cli.check import check_environment
from pyready.cli.explain import explain_question
from pyready.cli.diff import diff_command
from pyready.project_detection import detect_project_type, ProjectType

app = typer.Typer(
    name="onboardai",
    help="PyReady CLI - Project environment checker and assistant",
    add_completion=False,
)

console = Console()


@app.command()
def check(
    path: str = typer.Argument(
        ".",
        help="Path to project directory to check (defaults to current directory)",
    ),
    explain: bool = typer.Option(
        False,
        "--explain",
        "-e",
        help="Include AI-assisted explanations (requires GROQ_API_KEY)",
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Export report to file (.json or .md)",
    ),
):
    """
    Check the development environment for a project.
    
    Validates Python version, virtual environment, dependencies, and environment variables.
    Detects run command using deterministic analysis.
    
    With --explain flag, adds AI-assisted explanations of detected commands.
    With --output flag, exports report to JSON or Markdown format.
    """
    project_path = Path(path).resolve()
    
    if not project_path.exists():
        typer.echo(f"Error: Directory '{path}' does not exist.", err=True)
        raise typer.Exit(1)
    
    if not project_path.is_dir():
        typer.echo(f"Error: '{path}' is not a directory.", err=True)
        raise typer.Exit(1)
    
    # Detect project type first
    project_type = detect_project_type(project_path)
    
    # Display project type detection
    _display_project_detection(project_path, project_type)
    
    # Convert output to Path if provided
    output_path = Path(output) if output else None
    
    # Pass project_type to check_environment
    check_environment(project_path, project_type, enable_explanations=explain, output_path=output_path)


def _display_project_detection(project_path: Path, project_type: ProjectType) -> None:
    """Display project type detection results"""
    console.print(f"\n🔍 [bold]Project type detected:[/bold] [cyan]{project_type.value}[/cyan]")
    console.print("[dim]Evidence:[/dim]")
    
    if project_type == ProjectType.POETRY:
        if (project_path / "pyproject.toml").exists():
            console.print("  • pyproject.toml")
            console.print("  • [tool.poetry] section found")
    
    elif project_type == ProjectType.PIP_VENV:
        if (project_path / "requirements.txt").exists():
            console.print("  • requirements.txt")
        if (project_path / "requirements-dev.txt").exists():
            console.print("  • requirements-dev.txt")
        
        req_dir = project_path / "requirements"
        if req_dir.is_dir():
            txt_files = list(req_dir.glob("*.txt"))
            for f in txt_files[:3]:  # Show max 3
                console.print(f"  • requirements/{f.name}")
    
    elif project_type == ProjectType.SETUPTOOLS:
        if (project_path / "setup.py").exists():
            console.print("  • setup.py")
        if (project_path / "setup.cfg").exists():
            console.print("  • setup.cfg")
    
    elif project_type == ProjectType.UNKNOWN:
        console.print("  • No Python project markers found")
    
    console.print()  # Blank line


@app.command()
def diff(
    old_report: str = typer.Argument(
        ...,
        help="Path to older report JSON file"
    ),
    new_report: str = typer.Argument(
        ...,
        help="Path to newer report JSON file"
    ),
    output: str = typer.Option(
        None,
        "--output",
        "-o",
        help="Export diff to file (.json or .md)"
    ),
    policy: str = typer.Option(
        None,
        "--policy",
        "-p",
        help="Policy file to evaluate diff against (.yml, .yaml, or .json)"
    ),
    explain_policy: bool = typer.Option(
        False,
        "--explain-policy",
        help="Show detailed explanation of policy evaluation (requires --policy)"
    ),
):
    """
    Compare two PyReady reports and show what changed.
    
    Detects changes in:
    - Capabilities (gained/lost)
    - Project intent
    - Environment check status
    - Recommendations
    - Run command
    
    With --policy flag, evaluates changes against team-defined rules.
    With --explain-policy flag, shows why each rule did or didn't match.
    
    Exit codes:
    - 0: PASS (no violations or no policy)
    - 1: WARN (warnings detected)
    - 2: FAIL (failures detected or error)
    
    Example:
      pyready diff report-old.json report-new.json
      pyready diff report-old.json report-new.json --policy .pyready-policy.yml
      pyready diff report-old.json report-new.json --policy policy.yml --explain-policy
    """
    old_path = Path(old_report).resolve()
    new_path = Path(new_report).resolve()
    
    if not old_path.exists():
        typer.echo(f"Error: Old report not found: {old_report}", err=True)
        raise typer.Exit(2)
    
    if not new_path.exists():
        typer.echo(f"Error: New report not found: {new_report}", err=True)
        raise typer.Exit(2)
    
    # Warn if --explain-policy used without --policy
    if explain_policy and not policy:
        typer.echo("Warning: --explain-policy requires --policy flag", err=True)
        typer.echo("Ignoring --explain-policy", err=True)
        explain_policy = False
    
    # Convert paths
    output_path = Path(output) if output else None
    policy_path = Path(policy).resolve() if policy else None
    
    # Run diff command and get exit code
    exit_code = diff_command(old_path, new_path, output_path, policy_path, explain_policy)
    
    # Exit with appropriate code for CI/CD
    raise typer.Exit(exit_code)


@app.command()
def explain(
    question: str = typer.Argument(
        ...,
        help="Question to answer using project analysis"
    ),
    path: str = typer.Option(
        ".",
        "--path",
        "-p",
        help="Path to project directory (defaults to current directory)",
    ),
):
    """
    Answer questions about the project using pre-computed analysis.
    
    Supported question types:
    - Why is <package> required?
    - What runs when I start the project?
    - What breaks if I remove <file>?
    - Where is <module> used?
    
    Requires GROQ_API_KEY environment variable.
    """
    project_path = Path(path).resolve()
    
    if not project_path.exists():
        typer.echo(f"Error: Directory '{path}' does not exist.", err=True)
        raise typer.Exit(1)
    
    if not project_path.is_dir():
        typer.echo(f"Error: '{path}' is not a directory.", err=True)
        raise typer.Exit(1)
    
    explain_question(project_path, question)


if __name__ == "__main__":
    app()

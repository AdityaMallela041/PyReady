"""Explain command for Q&A over deterministic artifacts."""

import os
import sys
from pathlib import Path
from rich.console import Console

# Import backend modules
try:
    from pyready.qa.classifier import QuestionClassifier, QuestionType
    from pyready.qa.artifact_selector import ArtifactSelector
    from pyready.qa.answer_generator import AnswerGenerator
    from pyready.run_detection.detector import RunCommandDetector
    QA_AVAILABLE = True
except ImportError:
    QA_AVAILABLE = False

console = Console()


def is_groq_available() -> bool:
    """
    Check if Groq API key is configured.
    
    Returns:
        True if GROQ_API_KEY environment variable is set, False otherwise
    """
    return os.getenv("GROQ_API_KEY") is not None


def explain_question(project_path: Path, question: str) -> None:
    """
    Answer a question using pre-computed artifacts.
    
    This command REQUIRES Groq API access and will exit with error if unavailable.
    Unlike the optional --explain flag, this is the dedicated Q&A interface.
    
    Args:
        project_path: Path to project directory
        question: User's question
    """
    if not QA_AVAILABLE:
        console.print("\n❌ [red]Q&A system unavailable[/red]")
        console.print("  [dim]Backend modules not found[/dim]\n")
        return
    
    # PHASE 14.5: Explicit Groq availability check with helpful error
    if not is_groq_available():
        console.print("\n❌ [red]Error:[/red] GROQ_API_KEY environment variable not set")
        console.print("\nThe 'explain' command requires Groq API access.")
        console.print("Set your API key:")
        console.print("  export GROQ_API_KEY='your-key-here'")
        console.print("\nGet a free API key at: https://console.groq.com/keys")
        console.print()
        sys.exit(1)
    
    console.print(f"\n🤔 Question: [cyan]{question}[/cyan]\n")
    
    # Step 1: Classify question (deterministic)
    classifier = QuestionClassifier()
    question_type, entity = classifier.classify(question)
    
    if question_type == QuestionType.UNSUPPORTED:
        console.print("❌ [yellow]This question cannot be answered with the available analysis.[/yellow]\n")
        console.print("  [dim]Supported question types:[/dim]")
        console.print("    • Why is <package> required?")
        console.print("    • What runs when I start the project?")
        console.print("    • What breaks if I remove <file>?")
        console.print("    • Where is <module> used?\n")
        return
    
    console.print(f"  [dim]Question type: {question_type.value}[/dim]")
    if entity:
        console.print(f"  [dim]Entity: {entity}[/dim]")
    console.print()
    
    # Step 2: Select artifacts (deterministic)
    selector = ArtifactSelector(project_path)
    
    # Get run command if needed
    run_command_result = None
    if question_type == QuestionType.WHAT_RUNS:
        try:
            detector = RunCommandDetector(project_path)
            run_command_result = detector.detect()
        except Exception:
            pass
    
    artifacts = selector.select_artifacts(question_type, entity, run_command_result)
    
    # Check for errors
    if "error" in artifacts:
        console.print(f"❌ [yellow]{artifacts['error']}[/yellow]\n")
        return
    
    # Step 3: Generate answer (LLM-based phrasing)
    generator = AnswerGenerator()
    
    # PHASE 14.5: This should not happen since we checked earlier, but double-check
    if not generator.is_available():
        console.print("❌ [yellow]Answer generation unavailable (GROQ_API_KEY issue)[/yellow]\n")
        return
    
    console.print("  [dim]Generating answer...[/dim]\n")
    
    try:
        answer = generator.generate_answer(question, question_type, artifacts)
        
        if answer:
            console.print("💡 [bold]Answer:[/bold]\n")
            
            # Display answer with indentation
            for line in answer.split("\n"):
                if line.strip():
                    console.print(f"  {line}")
            
            console.print()
        else:
            console.print("❌ [yellow]Failed to generate answer[/yellow]\n")
    
    except Exception as e:
        # PHASE 14.5: Handle Groq errors gracefully
        error_msg = str(e)
        if "timed out" in error_msg.lower() or "timeout" in error_msg.lower():
            console.print("❌ [yellow]Answer generation timed out. Please try again.[/yellow]\n")
        else:
            console.print(f"❌ [yellow]Failed to generate answer: {error_msg}[/yellow]\n")


def explain_run_command(run_command: str, project_path: Path) -> str | None:
    """
    Generate natural language explanation of run command using Groq.
    
    This is used by the check command with --explain flag.
    Falls back to None if Groq is unavailable or fails.
    
    IMPORTANT: This is purely for human readability and does not affect any:
    - Detection logic
    - Classification logic
    - Validation logic
    - Policy matching
    - Exit codes
    
    Args:
        run_command: Detected run command to explain
        project_path: Path to project being analyzed
    
    Returns:
        Natural language explanation or None if unavailable
    """
    # PHASE 14.5: Early exit if Groq unavailable
    if not is_groq_available():
        return None
    
    try:
        from groq import Groq
        
        # Initialize Groq client
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        
        # Build prompt with deterministic context
        project_name = project_path.name
        
        prompt = f"""You are explaining a detected run command for a Python project.

Project: {project_name}
Run command: {run_command}

Provide a concise 2-3 sentence explanation of:
1. What this command does
2. Why it's structured this way

Keep it practical and specific to the command. Do not add warnings or recommendations."""
        
        # PHASE 14.5: Call Groq with explicit timeout
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a Python development assistant. Provide clear, concise explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=10  # PHASE 14.5: Explicit 10-second timeout
        )
        
        return response.choices[0].message.content.strip()
    
    except Exception as e:
        # PHASE 14.5: Silent fallback instead of crash
        # LLM errors should never break the CLI
        return None

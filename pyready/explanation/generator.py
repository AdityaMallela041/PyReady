"""Explanation generator for deterministic analysis results."""

from typing import Optional, List
from pathlib import Path

from pyready.llm.client import LLMClient, LLMError
from pyready.llm.groq_client import GroqClient
from pyready.run_detection.models import RunCommandResult


class ExplanationGenerator:
    """
    Generates human-friendly explanations for deterministic analysis results.
    
    IMPORTANT: This class NEVER makes decisions or adds new facts.
    It only explains what has already been determined by analysis.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize explanation generator.
        
        Args:
            llm_client: LLM client to use (defaults to GroqClient)
        """
        self.llm_client = llm_client or GroqClient()
    
    def is_available(self) -> bool:
        """Check if explanation generation is available."""
        return self.llm_client.is_available()
    
    def explain_run_command(
        self, 
        run_result: RunCommandResult,
        project_name: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate explanation for detected run command.
        
        Args:
            run_result: Run command detection result (from Phase 4)
            project_name: Optional project name for context
            
        Returns:
            Explanation string or None if generation fails
            
        Note:
            AI receives ONLY:
            - The detected command (already determined)
            - Evidence list (already collected)
            - Command type (already classified)
            
            AI does NOT:
            - Read repository files
            - Analyze code
            - Make decisions
        """
        if not self.is_available():
            return None
        
        if not run_result.has_command():
            # No command detected - explain why and what user can do
            return self._explain_no_command(run_result)
        
        # Build context from deterministic analysis only
        prompt = self._build_prompt(run_result, project_name)
        
        try:
            explanation = self.llm_client.generate(prompt, max_tokens=200)
            return explanation
        except LLMError:
            # LLM failure should not break the CLI
            return None
    
    def _build_prompt(
        self, 
        run_result: RunCommandResult,
        project_name: Optional[str]
    ) -> str:
        """
        Build prompt from deterministic context only.
        
        This method is the ONLY bridge between deterministic analysis and AI.
        It must pass ONLY facts that were already determined.
        """
        project_context = f" for the '{project_name}' project" if project_name else ""
        
        # Extract evidence details
        evidence_summary = []
        for evidence in run_result.evidence:
            evidence_summary.append(f"- {evidence.file_path}: {evidence.reason}")
        
        evidence_text = "\n".join(evidence_summary) if evidence_summary else "No additional evidence"
        
        prompt = f"""Explain this command{project_context} in 3-6 lines for a developer:

Command: {run_result.command}

Evidence:
{evidence_text}

Command type: {run_result.command_type.value}

Provide a clear, technical explanation of:
1. What this command does
2. What the key flags/options mean (if any)
3. When this command is typically used

Do not add recommendations or speculate beyond what is shown above."""
        
        return prompt
    
    def _explain_no_command(self, run_result: RunCommandResult) -> Optional[str]:
        """
        Explain why no command was detected.
        
        This is a fallback explanation when detection found nothing.
        """
        prompt = """Explain in 3-4 lines why a Python project might not have a detectable run command, and what a developer should check:

The automated detection looked for:
- Poetry scripts in pyproject.toml
- FastAPI applications (app = FastAPI())
- Flask applications (app = Flask(__name__))
- Python files with if __name__ == "__main__"

None of these patterns were found.

Keep the explanation practical and actionable."""
        
        try:
            explanation = self.llm_client.generate(prompt, max_tokens=150)
            return explanation
        except LLMError:
            return None

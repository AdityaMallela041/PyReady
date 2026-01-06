"""LLM-based answer generation using artifacts only."""

from typing import Dict, Any, Optional
import json

from pyready.llm.client import LLMClient, LLMError
from pyready.llm.groq_client import GroqClient
from .classifier import QuestionType


class AnswerGenerator:
    """
    Generates answers using LLM, constrained to pre-computed artifacts.
    
    CRITICAL: LLM receives ONLY artifact data, NEVER source code access.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize answer generator.
        
        Args:
            llm_client: LLM client (defaults to GroqClient)
        """
        self.llm_client = llm_client or GroqClient()
    
    def is_available(self) -> bool:
        """Check if LLM is available."""
        return self.llm_client.is_available()
    
    def generate_answer(
        self, 
        question: str,
        question_type: QuestionType,
        artifacts: Dict[str, Any]
    ) -> Optional[str]:
        """
        Generate answer from artifacts.
        
        Args:
            question: Original question
            question_type: Classified question type
            artifacts: Pre-selected artifacts
            
        Returns:
            Formatted answer string or None if generation fails
        """
        if not self.is_available():
            return None
        
        # Check for errors in artifacts
        if "error" in artifacts:
            return f"Cannot answer: {artifacts['error']}"
        
        # Build prompt based on question type
        prompt = self._build_prompt(question, question_type, artifacts)
        
        try:
            response = self.llm_client.generate(prompt, max_tokens=300)
            return response
        except LLMError:
            return None
    
    def _build_prompt(
        self, 
        question: str,
        question_type: QuestionType,
        artifacts: Dict[str, Any]
    ) -> str:
        """
        Build LLM prompt from artifacts.
        
        This is the ONLY bridge between artifacts and LLM.
        MUST NOT pass file paths for reading or any source code.
        """
        # Convert artifacts to JSON for structured context
        artifacts_json = json.dumps(artifacts, indent=2)
        
        base_instructions = """You are a technical assistant answering questions about a Python project.

CRITICAL RULES:
1. Use ONLY the provided artifacts below
2. Do NOT speculate or infer missing information
3. If artifacts don't contain enough information, say "Not enough information in the analysis"
4. Cite specific artifact fields in your answer
5. Format your answer as:
   
   Answer:
   <2-4 line factual explanation>
   
   Evidence:
   - <artifact>: <fact>
   - <artifact>: <fact>

6. Do NOT provide opinions or recommendations
"""
        
        # Question-specific instructions
        if question_type == QuestionType.WHY_REQUIRED:
            specific_instructions = """
Question type: "Why is X required?"

Check if the package appears in:
- dependencies (production)
- dev_dependencies (development only)

If found, explain its typical use case based on package name only.
If not found, state it's not listed as a dependency.
"""
        
        elif question_type == QuestionType.WHAT_RUNS:
            specific_instructions = """
Question type: "What runs when I start the project?"

Explain:
1. The detected run command
2. What the command does (based on command_type)
3. The entry point (based on evidence)

Use only the provided run_command, command_type, and evidence fields.
"""
        
        elif question_type == QuestionType.WHAT_BREAKS:
            specific_instructions = """
Question type: "What breaks if I remove X?"

Check if package is in dependencies.
If yes: State it's a direct dependency and may be used by the application.
If no: State it's not a declared dependency.

Do NOT scan code to find usage - only check dependency declarations.
"""
        
        elif question_type == QuestionType.WHERE_USED:
            specific_instructions = """
Question type: "Where is X used?"

Check if package is in dependencies.
If yes: State it's declared as a dependency.
If no: State it's not found in dependencies.

IMPORTANT: You do NOT have access to source code or import information.
Only report what's in the dependency declarations.
"""
        
        else:
            specific_instructions = "This question type is not supported."
        
        prompt = f"""{base_instructions}

{specific_instructions}

Question: {question}

Available Artifacts:
{artifacts_json}

Generate your answer now:"""
        
        return prompt

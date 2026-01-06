"""Artifact selection based on question type."""

from typing import Dict, Any, Optional, List
from pathlib import Path
import tomli

from .classifier import QuestionType


class ArtifactSelector:
    """
    Selects relevant pre-computed artifacts for a question.
    
    NEVER reads source code. ONLY uses deterministic analysis results.
    """
    
    def __init__(self, project_path: Path):
        """
        Initialize artifact selector.
        
        Args:
            project_path: Path to project root
        """
        self.project_path = project_path
        self.pyproject_path = project_path / "pyproject.toml"
    
    def select_artifacts(
        self, 
        question_type: QuestionType, 
        entity: Optional[str],
        run_command_result=None
    ) -> Dict[str, Any]:
        """
        Select artifacts relevant to question type.
        
        Args:
            question_type: Classified question type
            entity: Extracted entity (e.g., package name)
            run_command_result: Result from Phase 4 detection
            
        Returns:
            Dictionary of artifacts with only relevant data
        """
        if question_type == QuestionType.WHY_REQUIRED:
            return self._select_for_why_required(entity)
        
        elif question_type == QuestionType.WHAT_RUNS:
            return self._select_for_what_runs(run_command_result)
        
        elif question_type == QuestionType.WHAT_BREAKS:
            return self._select_for_what_breaks(entity)
        
        elif question_type == QuestionType.WHERE_USED:
            return self._select_for_where_used(entity)
        
        else:
            return {}
    
    def _select_for_why_required(self, entity: Optional[str]) -> Dict[str, Any]:
        """Select artifacts for 'Why is X required?' question."""
        if not entity:
            return {"error": "No package name specified"}
        
        artifacts = {
            "question_entity": entity,
            "dependencies": self._get_dependencies(),
            "dev_dependencies": self._get_dev_dependencies(),
        }
        
        return artifacts
    
    def _select_for_what_runs(self, run_command_result) -> Dict[str, Any]:
        """Select artifacts for 'What runs when I start?' question."""
        if not run_command_result:
            return {"error": "Run command not detected"}
        
        artifacts = {
            "run_command": run_command_result.command,
            "command_type": run_command_result.command_type.value,
            "detection_basis": run_command_result.detection_basis.value,
            "evidence": [
                {
                    "file": str(ev.file_path),
                    "reason": ev.reason,
                    "line": ev.line_number
                }
                for ev in run_command_result.evidence
            ]
        }
        
        return artifacts
    
    def _select_for_what_breaks(self, entity: Optional[str]) -> Dict[str, Any]:
        """Select artifacts for 'What breaks if I remove X?' question."""
        if not entity:
            return {"error": "No package name specified"}
        
        artifacts = {
            "question_entity": entity,
            "dependencies": self._get_dependencies(),
            "is_direct_dependency": self._is_direct_dependency(entity),
        }
        
        return artifacts
    
    def _select_for_where_used(self, entity: Optional[str]) -> Dict[str, Any]:
        """Select artifacts for 'Where is X used?' question."""
        if not entity:
            return {"error": "No package name specified"}
        
        artifacts = {
            "question_entity": entity,
            "dependencies": self._get_dependencies(),
            "is_direct_dependency": self._is_direct_dependency(entity),
        }
        
        return artifacts
    
    def _get_dependencies(self) -> Dict[str, str]:
        """Get production dependencies from pyproject.toml."""
        if not self.pyproject_path.exists():
            return {}
        
        try:
            with open(self.pyproject_path, "rb") as f:
                pyproject = tomli.load(f)
            
            deps = pyproject.get("tool", {}).get("poetry", {}).get("dependencies", {})
            # Remove python itself
            deps.pop("python", None)
            return deps
        except Exception:
            return {}
    
    def _get_dev_dependencies(self) -> Dict[str, str]:
        """Get dev dependencies from pyproject.toml."""
        if not self.pyproject_path.exists():
            return {}
        
        try:
            with open(self.pyproject_path, "rb") as f:
                pyproject = tomli.load(f)
            
            return pyproject.get("tool", {}).get("poetry", {}).get("group", {}).get("dev", {}).get("dependencies", {})
        except Exception:
            return {}
    
    def _is_direct_dependency(self, package_name: str) -> bool:
        """Check if package is a direct dependency."""
        deps = self._get_dependencies()
        dev_deps = self._get_dev_dependencies()
        
        # Normalize package name (handle case sensitivity)
        package_lower = package_name.lower()
        
        all_deps = {k.lower(): v for k, v in {**deps, **dev_deps}.items()}
        
        return package_lower in all_deps

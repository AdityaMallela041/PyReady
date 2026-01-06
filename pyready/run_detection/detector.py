"""Run command detection logic with deterministic, evidence-based approach."""

import ast
from pathlib import Path
from typing import Optional, List, Dict, Any
import tomli

from .models import RunCommandResult, EvidenceItem, RunCommandType, DetectionBasis


class RunCommandDetector:
    """Detects how to run a Python project using deterministic logic only."""
    
    def __init__(self, project_path: Path, project_type: str = "pip_venv"):
        """
        Initialize detector for a project.
        
        Args:
            project_path: Path to the project root directory
            project_type: Type of project (POETRY, pip_venv, etc.)
        """
        self.project_path = project_path
        self.project_type = project_type
        self.pyproject_path = project_path / "pyproject.toml"
    
    def _format_command(self, base_command: str) -> str:
        """
        Format command with appropriate prefix based on project type.
        
        Args:
            base_command: The base command without prefix
            
        Returns:
            Formatted command with correct prefix
        """
        if self.project_type == "POETRY":
            return f"poetry run {base_command}"
        else:
            # For pip_venv, npm, etc - no prefix needed
            return base_command
        
    def detect(self) -> RunCommandResult:
        """
        Detect run command using priority order.
        
        Priority:
        1. Poetry scripts (explicit)
        2. FastAPI app (pattern-based)
        3. Flask app (pattern-based)
        4. Direct Python execution (fallback)
        5. None (no safe command detected)
        
        Returns:
            RunCommandResult with command and evidence
        """
        # Priority 1: Poetry scripts
        result = self._detect_poetry_script()
        if result.has_command():
            return result
        
        # Priority 2: FastAPI app
        result = self._detect_fastapi()
        if result.has_command():
            return result
        
        # Priority 3: Flask app
        result = self._detect_flask()
        if result.has_command():
            return result
        
        # Priority 4: Direct Python execution
        result = self._detect_direct_python()
        if result.has_command():
            return result
        
        # No command detected
        return RunCommandResult(
            command=None,
            command_type=RunCommandType.NONE,
            evidence=[],
            detection_basis=DetectionBasis.NONE
        )
    
    def _detect_poetry_script(self) -> RunCommandResult:
        """
        Detect Poetry scripts from pyproject.toml.
        
        Looks for:
        - [tool.poetry.scripts] section
        - [project.scripts] section (PEP 621)
        
        Returns highest priority script (usually 'start', 'dev', or first found).
        """
        if not self.pyproject_path.exists():
            return RunCommandResult(
                command=None,
                command_type=RunCommandType.NONE,
                evidence=[],
                detection_basis=DetectionBasis.NONE
            )
        
        try:
            with open(self.pyproject_path, "rb") as f:
                pyproject = tomli.load(f)
            
            # Check [tool.poetry.scripts]
            poetry_scripts = pyproject.get("tool", {}).get("poetry", {}).get("scripts", {})
            if poetry_scripts:
                # Priority order for common script names
                priority_names = ["start", "dev", "run", "serve"]
                
                for name in priority_names:
                    if name in poetry_scripts:
                        return RunCommandResult(
                            command=f"poetry run {name}",
                            command_type=RunCommandType.POETRY_SCRIPT,
                            evidence=[
                                EvidenceItem(
                                    file_path="pyproject.toml",
                                    reason=f"[tool.poetry.scripts] defines '{name}' = '{poetry_scripts[name]}'"
                                )
                            ],
                            detection_basis=DetectionBasis.EXPLICIT
                        )
                
                # No priority name found, use first available
                first_script = next(iter(poetry_scripts.items()))
                return RunCommandResult(
                    command=f"poetry run {first_script[0]}",
                    command_type=RunCommandType.POETRY_SCRIPT,
                    evidence=[
                        EvidenceItem(
                            file_path="pyproject.toml",
                            reason=f"[tool.poetry.scripts] defines '{first_script[0]}' = '{first_script[1]}'"
                        )
                    ],
                    detection_basis=DetectionBasis.EXPLICIT
                )
            
            # Check [project.scripts] (PEP 621)
            project_scripts = pyproject.get("project", {}).get("scripts", {})
            if project_scripts:
                first_script = next(iter(project_scripts.items()))
                return RunCommandResult(
                    command=f"poetry run {first_script[0]}",
                    command_type=RunCommandType.POETRY_SCRIPT,
                    evidence=[
                        EvidenceItem(
                            file_path="pyproject.toml",
                            reason=f"[project.scripts] defines '{first_script[0]}' = '{first_script[1]}'"
                        )
                    ],
                    detection_basis=DetectionBasis.EXPLICIT
                )
        
        except Exception:
            pass
        
        return RunCommandResult(
            command=None,
            command_type=RunCommandType.NONE,
            evidence=[],
            detection_basis=DetectionBasis.NONE
        )
    
    def _detect_fastapi(self) -> RunCommandResult:
        """Detect FastAPI application entry point."""
        candidate_paths = [
            "app/main.py",
            "src/app/main.py",
            "src/main.py",
            "main.py",
            "api/main.py",
            "backend/main.py",
            "backend/app/main.py",
        ]
        
        evidence = []
        app_module = None
        
        for candidate in candidate_paths:
            file_path = self.project_path / candidate
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                
                fastapi_detected = False
                app_variable_detected = False
                line_number = None
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "fastapi":
                            for alias in node.names:
                                if alias.name == "FastAPI":
                                    fastapi_detected = True
                    
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "app":
                                if isinstance(node.value, ast.Call):
                                    if isinstance(node.value.func, ast.Name):
                                        if node.value.func.id == "FastAPI":
                                            app_variable_detected = True
                                            line_number = node.lineno
                
                if fastapi_detected and app_variable_detected:
                    module_path = candidate.replace("/", ".").replace("\\", ".").replace(".py", "")
                    app_module = f"{module_path}:app"
                    
                    evidence.append(
                        EvidenceItem(
                            file_path=candidate,
                            reason="FastAPI() instance assigned to 'app' variable",
                            line_number=line_number
                        )
                    )
                    break
            
            except Exception:
                continue
        
        if app_module:
            evidence.append(
                EvidenceItem(
                    file_path="pyproject.toml",
                    reason="no scripts defined"
                )
            )
            
            return RunCommandResult(
                command=self._format_command(f"uvicorn {app_module} --reload"),
                command_type=RunCommandType.FASTAPI,
                evidence=evidence,
                detection_basis=DetectionBasis.PATTERN_BASED
            )
        
        return RunCommandResult(
            command=None,
            command_type=RunCommandType.NONE,
            evidence=[],
            detection_basis=DetectionBasis.NONE
        )
    
    def _detect_flask(self) -> RunCommandResult:
        """Detect Flask application entry point."""
        candidate_paths = [
            "app.py",
            "main.py",
            "app/main.py",
            "src/app.py",
            "src/main.py",
            "api/app.py",
        ]
        
        evidence = []
        app_module = None
        
        for candidate in candidate_paths:
            file_path = self.project_path / candidate
            if not file_path.exists():
                continue
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=str(file_path))
                
                flask_detected = False
                app_variable_detected = False
                line_number = None
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom):
                        if node.module == "flask":
                            for alias in node.names:
                                if alias.name == "Flask":
                                    flask_detected = True
                    
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name) and target.id == "app":
                                if isinstance(node.value, ast.Call):
                                    if isinstance(node.value.func, ast.Name):
                                        if node.value.func.id == "Flask":
                                            app_variable_detected = True
                                            line_number = node.lineno
                
                if flask_detected and app_variable_detected:
                    module_path = candidate.replace("/", ".").replace("\\", ".").replace(".py", "")
                    app_module = module_path
                    
                    evidence.append(
                        EvidenceItem(
                            file_path=candidate,
                            reason="Flask(__name__) instance assigned to 'app' variable",
                            line_number=line_number
                        )
                    )
                    break
            
            except Exception:
                continue
        
        if app_module:
            evidence.append(
                EvidenceItem(
                    file_path="pyproject.toml",
                    reason="no scripts defined"
                )
            )
            
            return RunCommandResult(
                command=self._format_command(f"flask --app {app_module} run"),
                command_type=RunCommandType.FLASK,
                evidence=evidence,
                detection_basis=DetectionBasis.PATTERN_BASED
            )
        
        return RunCommandResult(
            command=None,
            command_type=RunCommandType.NONE,
            evidence=[],
            detection_basis=DetectionBasis.NONE
        )
    
    def _detect_direct_python(self) -> RunCommandResult:
        """Detect direct Python execution entry point."""
        candidate_names = ["main.py", "run.py", "start.py", "app.py", "__main__.py"]
        
        search_dirs = [
            self.project_path,
            self.project_path / "app",
            self.project_path / "src",
        ]
        
        evidence = []
        entry_point = None
        
        for search_dir in search_dirs:
            if not search_dir.exists():
                continue
            
            for candidate_name in candidate_names:
                file_path = search_dir / candidate_name
                if not file_path.exists():
                    continue
                
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=str(file_path))
                    
                    for node in ast.walk(tree):
                        if isinstance(node, ast.If):
                            if isinstance(node.test, ast.Compare):
                                if isinstance(node.test.left, ast.Name):
                                    if node.test.left.id == "__name__":
                                        relative_path = file_path.relative_to(self.project_path)
                                        entry_point = str(relative_path).replace("\\", "/")
                                        
                                        evidence.append(
                                            EvidenceItem(
                                                file_path=entry_point,
                                                reason='contains if __name__ == "__main__": block',
                                                line_number=node.lineno
                                            )
                                        )
                                        break
                    
                    if entry_point:
                        break
                
                except Exception:
                    continue
            
            if entry_point:
                break
        
        if entry_point:
            evidence.append(
                EvidenceItem(
                    file_path="pyproject.toml",
                    reason="no scripts defined"
                )
            )
            
            return RunCommandResult(
                command=self._format_command(f"python {entry_point}"),
                command_type=RunCommandType.DIRECT_PYTHON,
                evidence=evidence,
                detection_basis=DetectionBasis.FALLBACK
            )
        
        return RunCommandResult(
            command=None,
            command_type=RunCommandType.NONE,
            evidence=[],
            detection_basis=DetectionBasis.NONE
        )

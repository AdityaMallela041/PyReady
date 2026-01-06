"""Project capability detection - filesystem evidence only"""

from pathlib import Path
from typing import Dict, List, Set
import tomli

from pyready.schemas.capability_schema import ProjectCapabilities, CapabilityCheckResult


class CapabilityDetector:
    """
    Detects project capabilities based on filesystem evidence.
    
    Rules:
    - Only checks for presence of files/directories
    - Never executes code or makes assumptions
    - Returns False when evidence is absent (not when feature doesn't exist)
    """
    
    def __init__(self, project_path: Path):
        self.project_path = project_path.resolve()
        
    def detect(self) -> CapabilityCheckResult:
        """
        Detect all capabilities for the project.
        
        Returns:
            CapabilityCheckResult with boolean flags and evidence
        """
        evidence: Dict[str, List[str]] = {}
        warnings: List[str] = []
        
        # Capability 1: Python files
        has_python = self._detect_python_files(evidence)
        
        # Capability 2: Dependency declaration
        has_deps = self._detect_dependency_declaration(evidence)
        
        # Capability 3: Isolated environment
        has_venv = self._detect_isolated_environment(evidence)
        
        # Capability 4: Reproducible environment
        has_repro = self._detect_reproducible_environment(evidence)
        
        # Capability 5: Detectable entry point
        has_entry = self._detect_entrypoint(evidence)
        
        capabilities = ProjectCapabilities(
            has_python_files=has_python,
            has_dependency_declaration=has_deps,
            has_isolated_environment=has_venv,
            has_reproducible_environment=has_repro,
            has_detectable_entrypoint=has_entry,
            evidence=evidence
        )
        
        return CapabilityCheckResult(
            project_path=str(self.project_path),
            capabilities=capabilities,
            warnings=warnings
        )
    
    def _detect_python_files(self, evidence: Dict[str, List[str]]) -> bool:
        """
        Check if project contains Python source files.
        
        Evidence:
        - Any .py file (excluding __pycache__, .venv, venv, env)
        """
        exclude_dirs = {'__pycache__', '.venv', 'venv', 'env', '.git', 'node_modules'}
        found_files: List[str] = []
        
        try:
            for py_file in self.project_path.rglob('*.py'):
                # Skip excluded directories
                if any(excluded in py_file.parts for excluded in exclude_dirs):
                    continue
                
                relative_path = py_file.relative_to(self.project_path)
                found_files.append(str(relative_path))
                
                # Limit evidence to first 5 files
                if len(found_files) >= 5:
                    break
        except Exception:
            pass
        
        if found_files:
            evidence['has_python_files'] = found_files
            return True
        
        return False
    
    def _detect_dependency_declaration(self, evidence: Dict[str, List[str]]) -> bool:
        """
        Check if project declares dependencies in standard locations.
        
        Evidence:
        - requirements.txt
        - pyproject.toml with [tool.poetry.dependencies] or [project.dependencies]
        - setup.py with install_requires
        - Pipfile
        """
        found_files: List[str] = []
        
        # Check requirements.txt
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists() and req_file.is_file():
            found_files.append('requirements.txt')
        
        # Check pyproject.toml
        pyproject = self.project_path / 'pyproject.toml'
        if pyproject.exists() and pyproject.is_file():
            try:
                with open(pyproject, 'rb') as f:
                    data = tomli.load(f)
                
                # Poetry format
                if 'tool' in data and 'poetry' in data['tool']:
                    if 'dependencies' in data['tool']['poetry']:
                        found_files.append('pyproject.toml: [tool.poetry.dependencies]')
                
                # PEP 621 format
                if 'project' in data:
                    if 'dependencies' in data['project']:
                        found_files.append('pyproject.toml: [project.dependencies]')
            except Exception:
                pass
        
        # Check setup.py
        setup_file = self.project_path / 'setup.py'
        if setup_file.exists() and setup_file.is_file():
            try:
                with open(setup_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'install_requires' in content:
                        found_files.append('setup.py: install_requires')
            except Exception:
                pass
        
        # Check Pipfile
        pipfile = self.project_path / 'Pipfile'
        if pipfile.exists() and pipfile.is_file():
            found_files.append('Pipfile')
        
        if found_files:
            evidence['has_dependency_declaration'] = found_files
            return True
        
        return False
    
    def _detect_isolated_environment(self, evidence: Dict[str, List[str]]) -> bool:
        """
        Check if project has a virtual environment directory.
        
        Evidence:
        - venv/ directory with Python executable
        - .venv/ directory with Python executable
        - env/ directory with Python executable
        """
        found_dirs: List[str] = []
        
        venv_candidates = ['.venv', 'venv', 'env']
        
        for candidate in venv_candidates:
            venv_path = self.project_path / candidate
            if not venv_path.exists() or not venv_path.is_dir():
                continue
            
            # Check for Python executable (proof it's a real venv)
            has_python = (
                (venv_path / 'Scripts' / 'python.exe').exists() or
                (venv_path / 'bin' / 'python').exists()
            )
            
            if has_python:
                found_dirs.append(f'{candidate}/')
        
        if found_dirs:
            evidence['has_isolated_environment'] = found_dirs
            return True
        
        return False
    
    def _detect_reproducible_environment(self, evidence: Dict[str, List[str]]) -> bool:
        """
        Check if environment can be reproduced from declarations.
        
        Evidence:
        - poetry.lock (Poetry lock file)
        - Pipfile.lock (Pipenv lock file)
        - requirements.txt with pinned versions (==)
        """
        found_files: List[str] = []
        
        # Check for lock files
        lock_files = {
            'poetry.lock': 'poetry.lock',
            'Pipfile.lock': 'Pipfile.lock',
        }
        
        for filename, display in lock_files.items():
            lock_file = self.project_path / filename
            if lock_file.exists() and lock_file.is_file():
                found_files.append(display)
        
        # Check for pinned requirements.txt
        req_file = self.project_path / 'requirements.txt'
        if req_file.exists() and req_file.is_file():
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Look for pinned versions (==)
                    if '==' in content:
                        found_files.append('requirements.txt: pinned versions')
            except Exception:
                pass
        
        if found_files:
            evidence['has_reproducible_environment'] = found_files
            return True
        
        return False
    
    def _detect_entrypoint(self, evidence: Dict[str, List[str]]) -> bool:
        """
        Check if project has a detectable entry point.
        
        Evidence:
        - [tool.poetry.scripts] in pyproject.toml
        - [project.scripts] in pyproject.toml
        - main.py, run.py, app.py, __main__.py in root
        - FastAPI/Flask app instance (from run_detection results)
        
        Note: This only checks for FILE EXISTENCE, not code patterns.
        Code pattern detection is done by run_detection module.
        """
        found_entries: List[str] = []
        
        # Check pyproject.toml scripts
        pyproject = self.project_path / 'pyproject.toml'
        if pyproject.exists() and pyproject.is_file():
            try:
                with open(pyproject, 'rb') as f:
                    data = tomli.load(f)
                
                # Poetry scripts
                if 'tool' in data and 'poetry' in data['tool']:
                    if 'scripts' in data['tool']['poetry']:
                        scripts = data['tool']['poetry']['scripts']
                        if scripts:
                            script_names = list(scripts.keys())
                            found_entries.append(f'pyproject.toml: [tool.poetry.scripts] ({len(script_names)} defined)')
                
                # PEP 621 scripts
                if 'project' in data:
                    if 'scripts' in data['project']:
                        scripts = data['project']['scripts']
                        if scripts:
                            script_names = list(scripts.keys())
                            found_entries.append(f'pyproject.toml: [project.scripts] ({len(script_names)} defined)')
            except Exception:
                pass
        
        # Check common entry point file names
        entry_files = ['main.py', 'run.py', 'app.py', '__main__.py']
        
        for filename in entry_files:
            entry_file = self.project_path / filename
            if entry_file.exists() and entry_file.is_file():
                found_entries.append(filename)
        
        # Check common subdirectory patterns
        subdirs = ['app', 'src']
        for subdir in subdirs:
            for filename in entry_files:
                entry_file = self.project_path / subdir / filename
                if entry_file.exists() and entry_file.is_file():
                    found_entries.append(f'{subdir}/{filename}')
        
        if found_entries:
            evidence['has_detectable_entrypoint'] = found_entries
            return True
        
        return False

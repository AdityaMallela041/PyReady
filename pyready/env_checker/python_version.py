"""Python version checker"""

import sys
import re
from pathlib import Path
from typing import Optional, Tuple
import tomli


class PythonVersionChecker:
    """Checks if local Python version matches repository requirements"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
        self.current_version = self._get_current_version()
    
    @staticmethod
    def _get_current_version() -> Tuple[int, int, int]:
        """Get current Python version as tuple (major, minor, micro)"""
        return sys.version_info[:3]
    
    def check(self) -> dict:
        """
        Check Python version against repository requirements
        
        Returns:
            dict with keys: status, message, details, required_version, current_version
        """
        required = self._detect_required_version()
        
        if not required:
            return {
                "status": "WARN",
                "message": f"Python version: {self._format_version(self.current_version)}",
                "details": "No version requirement found in pyproject.toml or requirements.txt",
                "required_version": None,
                "current_version": self._format_version(self.current_version)
            }
        
        # Check if current version satisfies requirement
        satisfies = self._check_version_constraint(self.current_version, required)
        
        if satisfies:
            return {
                "status": "PASS",
                "message": f"Python version: {self._format_version(self.current_version)} (required: {required})",
                "details": None,
                "required_version": required,
                "current_version": self._format_version(self.current_version)
            }
        else:
            return {
                "status": "FAIL",
                "message": f"Python version mismatch: {self._format_version(self.current_version)} (required: {required})",
                "details": f"Current version does not satisfy requirement: {required}",
                "required_version": required,
                "current_version": self._format_version(self.current_version)
            }
    
    def _detect_required_version(self) -> Optional[str]:
        """
        Detect required Python version from pyproject.toml or requirements.txt
        
        Returns:
            Version string like "^3.9" or ">=3.10,<3.12" or None
        """
        # Try pyproject.toml first
        pyproject_path = self.repo_path / "pyproject.toml"
        if pyproject_path.exists():
            version = self._parse_pyproject_toml(pyproject_path)
            if version:
                return version
        
        # Fallback to requirements.txt
        requirements_path = self.repo_path / "requirements.txt"
        if requirements_path.exists():
            version = self._parse_requirements_txt(requirements_path)
            if version:
                return version
        
        return None
    
    def _parse_pyproject_toml(self, path: Path) -> Optional[str]:
        """Parse Python version from pyproject.toml"""
        try:
            with open(path, "rb") as f:
                data = tomli.load(f)
            
            # Check Poetry format: [tool.poetry.dependencies]
            if "tool" in data and "poetry" in data["tool"]:
                deps = data["tool"]["poetry"].get("dependencies", {})
                if "python" in deps:
                    return deps["python"]
            
            # Check PEP 621 format: [project]
            if "project" in data:
                requires_python = data["project"].get("requires-python")
                if requires_python:
                    return requires_python
            
        except Exception:
            pass
        
        return None
    
    def _parse_requirements_txt(self, path: Path) -> Optional[str]:
        """Parse Python version from requirements.txt (if specified)"""
        try:
            with open(path, "r") as f:
                for line in f:
                    line = line.strip()
                    # Look for lines like: python>=3.9
                    if line.startswith("python"):
                        match = re.match(r"python\s*([>=<~!]+.*)", line, re.IGNORECASE)
                        if match:
                            return match.group(1)
        except Exception:
            pass
        
        return None
    
    def _check_version_constraint(self, version: Tuple[int, int, int], constraint: str) -> bool:
        """
        Check if version satisfies constraint
        
        Supports:
        - ^3.9 (Poetry caret: >=3.9.0, <4.0.0)
        - >=3.9,<3.12 (multiple constraints)
        - >=3.9 (simple constraint)
        """
        # Handle Poetry caret operator (^)
        if constraint.startswith("^"):
            base_version = constraint[1:]
            return self._check_caret_constraint(version, base_version)
        
        # Handle multiple comma-separated constraints
        if "," in constraint:
            constraints = [c.strip() for c in constraint.split(",")]
            return all(self._check_single_constraint(version, c) for c in constraints)
        
        # Single constraint
        return self._check_single_constraint(version, constraint)
    
    def _check_caret_constraint(self, version: Tuple[int, int, int], base: str) -> bool:
        """
        Check caret constraint (Poetry style)
        ^3.9 means >=3.9.0, <4.0.0
        """
        parts = base.split(".")
        if len(parts) < 2:
            return False
        
        try:
            major = int(parts[0])
            minor = int(parts[1])
            
            # Must be >= base version
            if version[0] < major:
                return False
            if version[0] == major and version[1] < minor:
                return False
            
            # Must be < next major version
            if version[0] >= major + 1:
                return False
            
            return True
        except ValueError:
            return False
    
    def _check_single_constraint(self, version: Tuple[int, int, int], constraint: str) -> bool:
        """Check a single constraint like >=3.9 or <3.12"""
        # Extract operator and version
        match = re.match(r"([>=<~!]+)\s*(\d+)\.?(\d+)?\.?(\d+)?", constraint)
        if not match:
            return False
        
        operator = match.group(1)
        req_major = int(match.group(2))
        req_minor = int(match.group(3)) if match.group(3) else 0
        req_micro = int(match.group(4)) if match.group(4) else 0
        
        req_version = (req_major, req_minor, req_micro)
        
        if operator == ">=":
            return version >= req_version
        elif operator == ">":
            return version > req_version
        elif operator == "<=":
            return version <= req_version
        elif operator == "<":
            return version < req_version
        elif operator == "==":
            return version == req_version
        elif operator == "!=":
            return version != req_version
        
        return False
    
    @staticmethod
    def _format_version(version: Tuple[int, int, int]) -> str:
        """Format version tuple as string"""
        return f"{version[0]}.{version[1]}.{version[2]}"

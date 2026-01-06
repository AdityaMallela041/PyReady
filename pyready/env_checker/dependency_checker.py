"""Dependency installation checker"""

import subprocess
import sys
from pathlib import Path
from typing import Set
import tomli


class DependencyChecker:
    """Checks if required dependencies are installed"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def check(self) -> dict:
        """Check if dependencies are installed"""
        required_deps = self._get_required_dependencies()
        
        if not required_deps:
            has_pyproject = (self.repo_path / "pyproject.toml").exists()
            has_requirements = (self.repo_path / "requirements.txt").exists()
            
            if has_pyproject or has_requirements:
                return {
                    "status": "WARN",
                    "message": "Dependencies: unable to parse dependency files",
                    "details": "Found files but could not extract dependencies",
                    "missing_deps": [],
                    "installed_deps": []
                }
            else:
                return {
                    "status": "WARN",
                    "message": "Dependencies: no requirements found",
                    "details": "No pyproject.toml or requirements.txt found",
                    "missing_deps": [],
                    "installed_deps": []
                }
        
        installed_deps = self._get_installed_packages()
        
        missing = []
        installed = []
        
        for dep in required_deps:
            if not dep or not dep.strip():
                continue
                
            pkg_name = self._extract_package_name(dep)
            
            if not pkg_name:
                continue
            
            if pkg_name.lower() in installed_deps:
                installed.append(dep)
            else:
                missing.append(dep)
        
        total_deps = len(installed) + len(missing)
        
        if not missing:
            return {
                "status": "PASS",
                "message": f"Dependencies: all {total_deps} packages installed",
                "details": None,
                "missing_deps": [],
                "installed_deps": []
            }
        else:
            missing_formatted = ', '.join(missing[:5])
            if len(missing) > 5:
                missing_formatted += f", ... and {len(missing) - 5} more"
            
            return {
                "status": "FAIL",
                "message": f"Dependencies: {len(missing)} missing",
                "details": f"Missing packages: {missing_formatted}",
                "missing_deps": missing,
                "installed_deps": installed
            }
    
    def _get_required_dependencies(self) -> Set[str]:
        """Get list of required dependencies from repository"""
        deps = set()
        
        pyproject_path = self.repo_path / "pyproject.toml"
        if pyproject_path.exists():
            deps.update(self._parse_pyproject_toml(pyproject_path))
        
        requirements_path = self.repo_path / "requirements.txt"
        if requirements_path.exists():
            deps.update(self._parse_requirements_txt(requirements_path))
        
        return deps
    
    def _parse_pyproject_toml(self, path: Path) -> Set[str]:
        """Parse dependencies from pyproject.toml"""
        deps = set()
        
        try:
            with open(path, "rb") as f:
                data = tomli.load(f)
            
            if "tool" in data and "poetry" in data["tool"]:
                poetry_deps = data["tool"]["poetry"].get("dependencies", {})
                for pkg_name, version_spec in poetry_deps.items():
                    if pkg_name.lower() != "python":
                        deps.add(pkg_name)
            
            if "project" in data:
                project_deps = data["project"].get("dependencies", [])
                for dep_string in project_deps:
                    pkg_name = self._extract_package_name(dep_string)
                    if pkg_name:
                        deps.add(pkg_name)
        except Exception:
            pass
        
        return deps
    
    def _parse_requirements_txt(self, path: Path) -> Set[str]:
        """Parse dependencies from requirements.txt"""
        deps = set()
        
        try:
            encodings = ['utf-8', 'utf-16', 'utf-16-le', 'utf-16-be']
            content = None
            
            for encoding in encodings:
                try:
                    with open(path, "r", encoding=encoding) as f:
                        content = f.read()
                    break
                except (UnicodeDecodeError, UnicodeError):
                    continue
            
            if not content:
                return deps
            
            for line in content.split('\n'):
                if "#" in line:
                    line = line.split("#")[0]
                
                line = line.strip()
                
                if not line or line.startswith("-"):
                    continue
                
                if line:
                    deps.add(line)
        except Exception:
            pass
        
        return deps
    
    def _extract_package_name(self, dep_string: str) -> str:
        """Extract package name from dependency string"""
        if not dep_string:
            return ""
        
        result = dep_string.strip()
        
        # Handle extras like pydantic[email]
        if '[' in result:
            result = result.split('[')[0].strip()
        
        # Handle version specifiers
        for sep in ['>=', '<=', '==', '!=', '~=', '>', '<', '@', ';']:
            if sep in result:
                result = result.split(sep)[0].strip()
                break
        
        return result
    
    def _get_installed_packages(self) -> Set[str]:
        """Get list of installed packages in the target project's environment"""
        installed = set()
        
        # Try to find target venv's Python
        target_python = None
        for candidate in [".venv", "venv", "env"]:
            venv_path = self.repo_path / candidate
            if venv_path.exists() and venv_path.is_dir():
                if (venv_path / "Scripts" / "python.exe").exists():
                    target_python = str(venv_path / "Scripts" / "python.exe")
                    break
                elif (venv_path / "bin" / "python").exists():
                    target_python = str(venv_path / "bin" / "python")
                    break
        
        # If no target venv found, use current Python
        if not target_python:
            target_python = sys.executable
        
        try:
            result = subprocess.run(
                [target_python, "-m", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                import json
                packages = json.loads(result.stdout)
                for pkg in packages:
                    installed.add(pkg["name"].lower())
        except Exception:
            pass
        
        return installed

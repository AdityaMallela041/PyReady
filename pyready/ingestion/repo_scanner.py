"""Repository scanner for Python files"""

import os
from pathlib import Path
from typing import List


class RepoScanner:
    """Scans a local Python repository and collects all Python files"""
    
    IGNORED_DIRS = {
        ".git",
        "__pycache__",
        "venv",
        ".venv",
        "env",
        ".env",
        "node_modules",
        ".pytest_cache",
        ".mypy_cache",
        "build",
        "dist",
        ".tox",
    }
    
    def __init__(self, repo_path: str):
        """
        Initialize scanner with repository path
        
        Args:
            repo_path: Absolute or relative path to repository
        """
        self.repo_path = Path(repo_path).resolve()
        
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.repo_path}")
        
        if not self.repo_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {self.repo_path}")
    
    def scan(self) -> List[Path]:
        """
        Recursively scan repository and collect all Python files
        
        Returns:
            List of absolute paths to Python files
        """
        python_files = []
        
        for root, dirs, files in os.walk(self.repo_path):
            # Remove ignored directories from traversal
            dirs[:] = [d for d in dirs if d not in self.IGNORED_DIRS]
            
            # Collect .py files
            for file in files:
                if file.endswith(".py"):
                    file_path = Path(root) / file
                    python_files.append(file_path)
        
        return python_files
    
    def get_relative_path(self, file_path: Path) -> str:
        """
        Get path relative to repository root
        
        Args:
            file_path: Absolute path to file
            
        Returns:
            Relative path string
        """
        return str(file_path.relative_to(self.repo_path))

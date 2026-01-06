"""Virtual environment detector"""

import os
import sys
from pathlib import Path
from typing import Optional


class VenvDetector:
    """Detects virtual environment status"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def check(self, os_type: str) -> dict:
        """
        Check virtual environment status
        
        Args:
            os_type: Operating system type (windows, linux, macos)
            
        Returns:
            dict with keys: status, message, details, fix_command, is_active, venv_exists
        """
        # Don't check if current venv is active - check if target project HAS a venv
        venv_path = self._find_venv_directory()
        
        # Best case: venv exists in target project
        if venv_path:
            return {
                "status": "PASS",
                "message": "Virtual environment: found",
                "details": f"Found venv at: {venv_path}",
                "fix_command": None,
                "is_active": False,  # We can't determine if it's active from outside
                "venv_exists": True
            }
        
        # No venv found
        create_cmd = self._get_create_command(os_type)
        return {
            "status": "FAIL",
            "message": "Virtual environment: not found",
            "details": "No .venv or venv directory found",
            "fix_command": create_cmd,
            "is_active": False,
            "venv_exists": False
        }

    
    @staticmethod
    def _is_venv_active() -> bool:
        """
        Detect if a virtual environment is currently active
        
        Checks:
        - VIRTUAL_ENV environment variable
        - sys.prefix != sys.base_prefix
        """
        # Check environment variable
        if os.environ.get("VIRTUAL_ENV"):
            return True
        
        # Check if sys.prefix differs from base_prefix
        # In a venv, these will be different
        return sys.prefix != sys.base_prefix
    
    def _find_venv_directory(self) -> Optional[Path]:
        """
        Find virtual environment directory in repository
        
        Looks for:
        - .venv/
        - venv/
        - env/
        - .env/
        """
        candidates = [".venv", "venv", "env", ".env"]
        
        for candidate in candidates:
            venv_path = self.repo_path / candidate
            if venv_path.exists() and venv_path.is_dir():
                # Verify it's actually a venv by checking for key files
                if self._is_valid_venv(venv_path):
                    return venv_path
        
        return None
    
    @staticmethod
    def _is_valid_venv(path: Path) -> bool:
        """
        Verify directory is a valid virtual environment
        
        Checks for presence of:
        - Scripts/ (Windows) or bin/ (Unix)
        - pyvenv.cfg file
        """
        has_scripts = (path / "Scripts").exists() or (path / "bin").exists()
        has_config = (path / "pyvenv.cfg").exists()
        
        return has_scripts or has_config
    
    def _get_activate_command(self, venv_path: Path, os_type: str) -> str:
        """
        Get activation command based on OS
        
        Args:
            venv_path: Path to venv directory
            os_type: Operating system type
        
        Returns:
            Activation command string
        """
        venv_name = venv_path.name
        
        if os_type == "windows":
            return f"{venv_name}\\Scripts\\activate"
        else:  # linux or macos
            return f"source {venv_name}/bin/activate"
    
    @staticmethod
    def _get_create_command(os_type: str) -> str:
        """
        Get venv creation and activation command
        
        Args:
            os_type: Operating system type
        
        Returns:
            Command to create and activate venv
        """
        if os_type == "windows":
            return "python -m venv .venv && .venv\\Scripts\\activate"
        else:  # linux or macos
            return "python -m venv .venv && source .venv/bin/activate"

"""Environment variables checker"""

import os
from pathlib import Path
from typing import Set, List


class EnvVarsChecker:
    """Checks if required environment variables are set"""
    
    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path)
    
    def check(self) -> dict:
        """
        Check if required environment variables are set
        
        Returns:
            dict with keys: status, message, details, missing_vars, set_vars
        """
        # Check what env files exist
        env_file = self.repo_path / ".env"
        env_example = self.repo_path / ".env.example"
        env_template = self.repo_path / ".env.template"
        
        has_env = env_file.exists()
        has_example = env_example.exists()
        has_template = env_template.exists()
        
        # Get required vars from example/template files
        required_vars = self._get_required_env_vars()
        
        # Case 1: No env files at all
        if not has_env and not has_example and not has_template:
            return {
                "status": "PASS",
                "message": "Environment variables: no requirements found",
                "details": "No .env, .env.example, or .env.template files found",
                "missing_vars": [],
                "set_vars": []
            }
        
        # Case 2: Has .env but no example/template (can't validate)
        if has_env and not required_vars:
            # Count vars in .env
            env_vars = self._parse_env_file(env_file)
            return {
                "status": "PASS",
                "message": f"Environment variables: .env found with {len(env_vars)} variables",
                "details": "No .env.example or .env.template to validate against",
                "missing_vars": [],
                "set_vars": list(env_vars)
            }
        
        # Case 3: Has example/template but no .env
        if required_vars and not has_env:
            return {
                "status": "FAIL",
                "message": "Environment variables: .env file missing",
                "details": f"Found {len(required_vars)} required variables in .env.example/.env.template but .env not found",
                "missing_vars": list(required_vars),
                "set_vars": []
            }
        
        # Case 4: Has both - validate
        set_vars_in_env = self._parse_env_file(env_file)
        
        missing = []
        set_vars = []
        
        for var in required_vars:
            if var in set_vars_in_env:
                set_vars.append(var)
            else:
                missing.append(var)
        
        if not missing:
            return {
                "status": "PASS",
                "message": f"Environment variables: all {len(required_vars)} variables set in .env",
                "details": None,
                "missing_vars": [],
                "set_vars": set_vars
            }
        else:
            return {
                "status": "FAIL",
                "message": f"Environment variables: {len(missing)} missing from .env",
                "details": f"Missing: {', '.join(missing[:5])}{'...' if len(missing) > 5 else ''}",
                "missing_vars": missing,
                "set_vars": set_vars
            }
    
    def _get_required_env_vars(self) -> Set[str]:
        """
        Get list of required environment variables
        
        Scans:
        - .env.example
        - .env.template
        
        Returns:
            Set of variable names
        """
        vars_set = set()
        
        # Check .env.example
        env_example = self.repo_path / ".env.example"
        if env_example.exists():
            vars_set.update(self._parse_env_file(env_example))
        
        # Check .env.template
        env_template = self.repo_path / ".env.template"
        if env_template.exists():
            vars_set.update(self._parse_env_file(env_template))
        
        return vars_set
    
    @staticmethod
    def _parse_env_file(path: Path) -> Set[str]:
        """
        Parse environment variable names from .env file
        
        Extracts variable names from lines like:
        - VAR_NAME=value
        - VAR_NAME=
        - # VAR_NAME=value (commented)
        
        Returns:
            Set of variable names
        """
        vars_set = set()
        
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines
                    if not line:
                        continue
                    
                    # Remove leading comment marker for commented lines
                    if line.startswith("#"):
                        line = line[1:].strip()
                    
                    # Look for VAR=value pattern
                    if "=" in line:
                        var_name = line.split("=")[0].strip()
                        # Validate it's a valid variable name (alphanumeric + underscore/hyphen)
                        if var_name and var_name.replace("_", "").replace("-", "").isalnum():
                            vars_set.add(var_name)
        
        except Exception:
            pass
        
        return vars_set

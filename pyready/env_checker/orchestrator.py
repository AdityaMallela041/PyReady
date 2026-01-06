"""Environment checker orchestrator"""

import platform
from pathlib import Path
from typing import List

from pyready.schemas.env_schema import CheckResult, CheckStatus, EnvironmentCheckReport
from pyready.schemas.capability_schema import ProjectCapabilities
from pyready.env_checker.python_version import PythonVersionChecker
from pyready.env_checker.venv_detector import VenvDetector
from pyready.env_checker.dependency_checker import DependencyChecker
from pyready.env_checker.env_vars_checker import EnvVarsChecker
from pyready.env_checker.expectations import CheckExpectations, create_skip_result, downgrade_to_warn
from pyready.project_detection.capabilities import CapabilityDetector


class EnvironmentChecker:
    """Orchestrates all environment checks with capability-aware expectations"""
    
    def __init__(self, repo_path: str, project_type: str = "pip_venv"):
        self.repo_path = Path(repo_path).resolve()
        self.project_type = project_type
        self.os_type = self._detect_os()
        
        if not self.repo_path.exists():
            raise FileNotFoundError(f"Repository path does not exist: {self.repo_path}")
    
    def run_checks(self) -> EnvironmentCheckReport:
        """
        Run all environment checks with capability-aware expectations.
        
        Returns:
            EnvironmentCheckReport with all check results
        """
        checks: List[CheckResult] = []
        
        # Detect project capabilities first
        capability_detector = CapabilityDetector(self.repo_path)
        capability_result = capability_detector.detect()
        capabilities = capability_result.capabilities
        
        # Create expectation policy based on capabilities
        expectations = CheckExpectations(capabilities)
        
        # Run checks with expectations
        checks.append(self._check_python_version(expectations))
        checks.append(self._check_virtual_environment(expectations))
        checks.extend(self._check_dependencies(expectations))
        checks.extend(self._check_env_vars(expectations))
        
        summary = self._calculate_summary(checks)
        
        return EnvironmentCheckReport(
            repo_path=str(self.repo_path),
            os_type=self.os_type,
            checks=checks,
            summary=summary
        )
    
    def _check_python_version(self, expectations: CheckExpectations) -> CheckResult:
        """Check Python version with capability awareness"""
        
        # Consult expectations
        should_run, skip_reason = expectations.should_check_python_version()
        
        if not should_run:
            return CheckResult(
                category="Python Version",
                status=CheckStatus.INFO,
                message="Check skipped",
                details=skip_reason,
                fix_command=None
            )
        
        # Run the actual check
        checker = PythonVersionChecker(str(self.repo_path))
        result = checker.check()
        
        # If no requirement found, use INFO status
        if result["status"] == "WARN" and "No" in result["message"]:
            return CheckResult(
                category="Python Version",
                status=CheckStatus.INFO,
                message=result["message"],
                details=result.get("details"),
                fix_command=None
            )
        
        return CheckResult(
            category="Python Version",
            status=CheckStatus[result["status"]],
            message=result["message"],
            details=result.get("details"),
            fix_command=None
        )
    
    def _check_virtual_environment(self, expectations: CheckExpectations) -> CheckResult:
        """Check virtual environment with capability awareness"""
        
        # Consult expectations
        should_run, skip_reason = expectations.should_check_virtual_environment()
        
        if not should_run:
            return CheckResult(
                category="Virtual Environment",
                status=CheckStatus.INFO,
                message="Check skipped",
                details=skip_reason,
                fix_command=None
            )
        
        # Run the actual check
        detector = VenvDetector(str(self.repo_path))
        result = detector.check(self.os_type)
        
        # If venv not found, downgrade to WARN
        if result["status"] == "FAIL":
            severity = expectations.virtual_environment_missing_severity()
            return CheckResult(
                category="Virtual Environment",
                status=CheckStatus[severity],
                message=result["message"],
                details="Virtual environment recommended for projects with dependencies",
                fix_command=result.get("fix_command")
            )
        
        return CheckResult(
            category="Virtual Environment",
            status=CheckStatus[result["status"]],
            message=result["message"],
            details=result.get("details"),
            fix_command=result.get("fix_command")
        )
    
    def _check_dependencies(self, expectations: CheckExpectations) -> List[CheckResult]:
        """Check dependencies with capability awareness"""
        
        # Consult expectations
        should_run, skip_reason = expectations.should_check_dependencies()
        
        if not should_run:
            return [CheckResult(
                category="Dependencies",
                status=CheckStatus.INFO,
                message="Check skipped",
                details=skip_reason,
                fix_command=None
            )]
        
        # Check if we can actually verify dependencies
        if not expectations.can_verify_dependencies():
            return [CheckResult(
                category="Dependencies",
                status=CheckStatus.WARN,
                message="Dependencies declared but cannot verify",
                details="Isolated environment required to verify installed packages",
                fix_command=self._get_dependency_fix_command([])
            )]
        
        # Run the actual check
        checker = DependencyChecker(str(self.repo_path))
        result = checker.check()
        
        checks = []
        checks.append(CheckResult(
            category="Dependencies",
            status=CheckStatus[result["status"]],
            message=result["message"],
            details=result.get("details"),
            fix_command=self._get_dependency_fix_command(result["missing_deps"])
        ))
        
        return checks
    
    def _check_env_vars(self, expectations: CheckExpectations) -> List[CheckResult]:
        """Check environment variables (always runs)"""
        
        checker = EnvVarsChecker(str(self.repo_path))
        result = checker.check()
        
        checks = []
        
        # Convert WARN about no requirements to INFO
        status = result["status"]
        if status == "WARN" and "no requirements" in result["message"].lower():
            status = "INFO"
        
        checks.append(CheckResult(
            category="Environment Variables",
            status=CheckStatus[status],
            message=result["message"],
            details=result.get("details"),
            fix_command=self._get_env_vars_fix_command(result["missing_vars"])
        ))
        
        return checks
    
    def _get_dependency_fix_command(self, missing_deps: List[str]) -> str:
        """Generate fix command for missing dependencies"""
        if not missing_deps:
            return None
        
        if (self.repo_path / "poetry.lock").exists():
            return "poetry install"
        
        if len(missing_deps) == 1:
            return f"pip install {missing_deps[0]}"
        elif len(missing_deps) <= 3:
            return f"pip install {' '.join(missing_deps)}"
        else:
            return "pip install -r requirements.txt"
    
    @staticmethod
    def _get_env_vars_fix_command(missing_vars: List[str]) -> str:
        """Generate fix command for missing environment variables"""
        if not missing_vars:
            return None
        
        if len(missing_vars) == 1:
            return f"Set {missing_vars[0]} in your environment or .env file"
        else:
            return f"Set {len(missing_vars)} variables in your environment or .env file"
    
    @staticmethod
    def _detect_os() -> str:
        """Detect operating system"""
        system = platform.system().lower()
        if system == "windows":
            return "windows"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            return "linux"  # Default fallback
    
    @staticmethod
    def _calculate_summary(checks: List[CheckResult]) -> dict:
        """Calculate summary statistics"""
        summary = {
            "total": len(checks),
            "passed": 0,
            "failed": 0,
            "warnings": 0
        }
        
        for check in checks:
            if check.status == CheckStatus.PASS:
                summary["passed"] += 1
            elif check.status == CheckStatus.FAIL:
                summary["failed"] += 1
            elif check.status == CheckStatus.WARN:
                summary["warnings"] += 1
            # INFO status doesn't count toward any category
        
        return summary

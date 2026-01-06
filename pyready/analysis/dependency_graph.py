"""Dependency graph builder for repository analysis"""

from pathlib import Path
from typing import List
from pyready.schemas.repo_schema import PythonFile, ModuleDependency, RepositoryGraph
from pyready.ingestion.repo_scanner import RepoScanner
from pyready.analysis.ast_parser import ASTParser


class DependencyGraphBuilder:
    """Builds a dependency graph from repository analysis"""
    
    def __init__(self, repo_path: str):
        """
        Initialize graph builder
        
        Args:
            repo_path: Path to repository
        """
        self.repo_path = repo_path
        self.scanner = RepoScanner(repo_path)
    
    def build(self) -> RepositoryGraph:
        """
        Build complete repository dependency graph
        
        Returns:
            RepositoryGraph with all analysis results
        """
        # Scan repository for Python files
        python_files = self.scanner.scan()
        
        # Initialize result containers
        analyzed_files = []
        dependencies = []
        entry_points = []
        errors = []
        
        # Analyze each file
        for file_path in python_files:
            try:
                # Parse file
                parse_result = ASTParser.parse_file(file_path)
                
                # Get relative path
                relative_path = self.scanner.get_relative_path(file_path)
                
                # Determine if entry point
                is_entry = (
                    parse_result["has_main_block"] or 
                    ASTParser.is_entry_point_file(file_path)
                )
                
                # Create PythonFile object
                python_file = PythonFile(
                    path=str(file_path),
                    relative_path=relative_path,
                    imports=parse_result["imports"],
                    functions=parse_result["functions"],
                    classes=parse_result["classes"],
                    is_entry_point=is_entry,
                    parse_error=parse_result["error"]
                )
                
                analyzed_files.append(python_file)
                
                # Track entry points
                if is_entry:
                    entry_points.append(relative_path)
                
                # Build dependency edges
                for imported_module in parse_result["imports"]:
                    dependency = ModuleDependency(
                        source=relative_path,
                        target=imported_module,
                        import_type="import"
                    )
                    dependencies.append(dependency)
                
                # Track parse errors
                if parse_result["error"]:
                    errors.append(f"{relative_path}: {parse_result['error']}")
                    
            except Exception as e:
                # Catch any unexpected errors during file processing
                relative_path = self.scanner.get_relative_path(file_path)
                error_msg = f"{relative_path}: Unexpected error: {str(e)}"
                errors.append(error_msg)
        
        # Build final graph
        graph = RepositoryGraph(
            repo_path=str(self.scanner.repo_path),
            total_files=len(analyzed_files),
            files=analyzed_files,
            dependencies=dependencies,
            entry_points=entry_points,
            errors=errors
        )
        
        return graph

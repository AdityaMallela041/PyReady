"""Pydantic schemas for repository analysis"""

from typing import List, Optional
from pydantic import BaseModel, Field


class PythonFile(BaseModel):
    """Represents a single Python file in the repository"""
    
    path: str = Field(..., description="Absolute path to the Python file")
    relative_path: str = Field(..., description="Path relative to repository root")
    imports: List[str] = Field(default_factory=list, description="List of imported modules")
    functions: List[str] = Field(default_factory=list, description="List of function names defined")
    classes: List[str] = Field(default_factory=list, description="List of class names defined")
    is_entry_point: bool = Field(default=False, description="Whether file contains __main__ or is main.py/app.py/run.py")
    parse_error: Optional[str] = Field(default=None, description="Error message if file failed to parse")


class ModuleDependency(BaseModel):
    """Represents an import relationship between modules"""
    
    source: str = Field(..., description="Source file path (relative)")
    target: str = Field(..., description="Imported module name")
    import_type: str = Field(..., description="Type of import: 'import' or 'from'")


class RepositoryGraph(BaseModel):
    """Complete repository analysis result"""
    
    repo_path: str = Field(..., description="Absolute path to repository root")
    total_files: int = Field(..., description="Total number of Python files found")
    files: List[PythonFile] = Field(default_factory=list, description="List of analyzed Python files")
    dependencies: List[ModuleDependency] = Field(default_factory=list, description="Import relationships")
    entry_points: List[str] = Field(default_factory=list, description="List of detected entry point files")
    errors: List[str] = Field(default_factory=list, description="List of errors encountered during analysis")

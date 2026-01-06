"""AST-based Python code parser"""

import ast
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class ASTParser:
    """Parses Python files using AST to extract structure"""
    
    @staticmethod
    def parse_file(file_path: Path) -> Dict:
        """
        Parse a Python file and extract imports, functions, classes
        
        Args:
            file_path: Path to Python file
            
        Returns:
            Dictionary with extracted information:
            {
                "imports": List[str],
                "functions": List[str],
                "classes": List[str],
                "has_main_block": bool,
                "error": Optional[str]
            }
        """
        result = {
            "imports": [],
            "functions": [],
            "classes": [],
            "has_main_block": False,
            "error": None
        }
        
        try:
            # Read file content
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse AST
            tree = ast.parse(content, filename=str(file_path))
            
            # Extract information
            result["imports"] = ASTParser._extract_imports(tree)
            result["functions"] = ASTParser._extract_functions(tree)
            result["classes"] = ASTParser._extract_classes(tree)
            result["has_main_block"] = ASTParser._detect_main_block(tree)
            
        except SyntaxError as e:
            result["error"] = f"SyntaxError: {str(e)}"
        except UnicodeDecodeError as e:
            result["error"] = f"UnicodeDecodeError: {str(e)}"
        except Exception as e:
            result["error"] = f"Unexpected error: {str(e)}"
        
        return result
    
    @staticmethod
    def _extract_imports(tree: ast.AST) -> List[str]:
        """Extract all import statements from AST"""
        imports = []
        
        for node in ast.walk(tree):
            # Handle: import module
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            
            # Handle: from module import ...
            elif isinstance(node, ast.ImportFrom):
                if node.module:  # module can be None for relative imports like "from . import x"
                    imports.append(node.module)
        
        return list(set(imports))  # Remove duplicates
    
    @staticmethod
    def _extract_functions(tree: ast.AST) -> List[str]:
        """Extract all function definitions from AST (top-level only)"""
        functions = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                functions.append(node.name)
        
        return functions
    
    @staticmethod
    def _extract_classes(tree: ast.AST) -> List[str]:
        """Extract all class definitions from AST (top-level only)"""
        classes = []
        
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
        
        return classes
    
    @staticmethod
    def _detect_main_block(tree: ast.AST) -> bool:
        """
        Detect if file contains: if __name__ == "__main__"
        
        Looks for:
        - if __name__ == "__main__":
        - if "__main__" == __name__:
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check if condition is a comparison
                if isinstance(node.test, ast.Compare):
                    compare = node.test
                    
                    # Check left side is __name__
                    left_is_name = (
                        isinstance(compare.left, ast.Name) and 
                        compare.left.id == "__name__"
                    )
                    
                    # Check right side is "__main__"
                    right_is_main = (
                        len(compare.comparators) > 0 and
                        isinstance(compare.comparators[0], ast.Constant) and
                        compare.comparators[0].value == "__main__"
                    )
                    
                    # Check operators (should be == or !=, but we only care about ==)
                    is_equal = any(isinstance(op, ast.Eq) for op in compare.ops)
                    
                    if (left_is_name and right_is_main and is_equal):
                        return True
                    
                    # Also check reverse: if "__main__" == __name__
                    left_is_main = (
                        isinstance(compare.left, ast.Constant) and 
                        compare.left.value == "__main__"
                    )
                    right_is_name = (
                        len(compare.comparators) > 0 and
                        isinstance(compare.comparators[0], ast.Name) and
                        compare.comparators[0].id == "__name__"
                    )
                    
                    if (left_is_main and right_is_name and is_equal):
                        return True
        
        return False
    
    @staticmethod
    def is_entry_point_file(file_path: Path) -> bool:
        """
        Check if filename suggests it's an entry point
        
        Entry point files: main.py, app.py, run.py, __main__.py
        """
        entry_point_names = {"main.py", "app.py", "run.py", "__main__.py"}
        return file_path.name in entry_point_names

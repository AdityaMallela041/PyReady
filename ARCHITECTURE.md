# 🏗️ PyReady Architecture

**Technical Design & Implementation Guide**

Version: 0.2.0  
Last Updated: January 6, 2026

---

## 📋 Table of Contents

- [Overview](#overview)
- [Design Principles](#design-principles)
- [System Architecture](#system-architecture)
- [Core Modules](#core-modules)
- [Data Flow](#data-flow)
- [Schema Design](#schema-design)
- [Determinism Guarantees](#determinism-guarantees)
- [Extension Points](#extension-points)
- [Performance Considerations](#performance-considerations)
- [Testing Strategy](#testing-strategy)

---

## 🎯 Overview

PyReady is built as a **modular, deterministic analysis pipeline** that transforms filesystem input into structured reports through a series of pure, composable functions.

### **Core Philosophy**

```
Input (Filesystem) → Detection → Analysis → Validation → Report → Output
         ↓              ↓           ↓            ↓          ↓        ↓
    Read-only      Evidence    Structured    Pass/Warn   JSON     Exit Code
                   Collection   Data         /Fail       Schema
```

**Key Insight:** Every step is deterministic, testable, and auditable.

---

## 🔑 Design Principles

### **1. Determinism First**
- No randomness, no timestamps in comparisons
- Stable sorting (lexicographic ordering)
- Reproducible outputs (same input = same output)
- No external API calls in core logic

### **2. Static Analysis Only**
- Filesystem inspection only
- No `import` statements from target projects
- No code execution or `eval()`
- AST parsing for Python files (read-only)

### **3. Fail-Safe Architecture**
- Graceful degradation (optional features fail silently)
- Clear boundaries between deterministic core and optional AI
- Validation at every layer (Pydantic schemas)
- Explicit error handling with typed exceptions

### **4. Composability**
- Small, single-purpose functions
- Functional programming patterns (map, filter, reduce)
- Dependency injection for testability
- Clear interfaces between modules

---

## 🏛️ System Architecture

### **High-Level Components**

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  (Typer) - User interface, argument parsing, output         │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Orchestration Layer                      │
│  Coordinates modules, manages data flow, error handling     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌───────────────┬─────────────────┬──────────────────────────┐
│  Detection    │   Analysis      │   Validation             │
│  - Project    │   - AST Parser  │   - Python Version       │
│    Type       │   - Dependency  │   - Virtual Env          │
│  - Capability │     Graph       │   - Dependencies         │
│  - Intent     │   - Run Command │   - Env Variables        │
└───────────────┴─────────────────┴──────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Reporting Layer                          │
│  Generate reports, compute diffs, export formats            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Policy Engine                           │
│  Evaluate rules, generate explanations (deterministic)      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Optional: AI Layer (Groq)                   │
│  Natural language Q&A, run command explanations             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🧩 Core Modules

### **1. CLI Module** (`pyready/cli/`)

**Purpose:** User interface and command routing

**Files:**
- `main.py` - Typer app, command registration
- `check.py` - Environment check command
- `diff.py` - Report comparison command
- `explain.py` - Q&A command (AI-powered)

**Key Design:**
```python
# Command pattern - each command is independent
@app.command()
def check(path: str, output: Optional[str] = None, explain: bool = False):
    # 1. Validate inputs
    # 2. Orchestrate detection & validation
    # 3. Generate report
    # 4. Optionally export
    # 5. Always exit 0 (no enforcement)
```

**Exit Code Contract:**
- `check`: Always 0 (analysis only)
- `diff` without policy: Always 0
- `diff` with policy: 0 (PASS), 1 (WARN), 2 (FAIL)
- `explain`: 0 (success), 2 (error)

---

### **2. Project Detection** (`pyready/project_detection/`)

**Purpose:** Identify project type and capabilities

**Files:**
- `detector.py` - Main detection logic
- `capabilities.py` - Capability checks (venv, lock files, etc.)
- `evidence.py` - Evidence collection functions
- `models.py` - Detection result models

**Detection Strategy:**
```python
def detect_project_type(path: Path) -> ProjectType:
    """
    Deterministic project type detection.
    
    Priority order:
    1. poetry (pyproject.toml + [tool.poetry])
    2. pipenv (Pipfile)
    3. conda (environment.yml)
    4. pip_venv (requirements.txt)
    5. script (single .py file)
    """
    # Check files in stable order (alphabetical)
    # Return first match
    # Evidence = exact files found + matching content
```

**Capability Detection:**
```python
def detect_capabilities(path: Path) -> CapabilityReport:
    """
    Detects:
    - has_python_files: any *.py files
    - has_dependency_declaration: requirements.txt, pyproject.toml, etc.
    - has_isolated_environment: venv/, .venv/, etc.
    - has_reproducible_environment: poetry.lock, Pipfile.lock, etc.
    - has_entry_point: __main__.py, pyproject.toml scripts, etc.
    """
    # Pure filesystem checks
    # No imports, no execution
    # Evidence-based (list exact files found)
```

---

### **3. Project Intent** (`pyready/project_intent/`)

**Purpose:** Classify project purpose

**Files:**
- `classifier.py` - Intent classification logic
- `models.py` - Intent types and models

**Classification Rules:**
```python
def classify_intent(capabilities: CapabilityReport) -> ProjectIntent:
    """
    Deterministic classification:
    
    1. SERVICE: 
       - Has entry point
       - Has dependencies
       - Has service config (Dockerfile, docker-compose.yml, etc.)
    
    2. APPLICATION:
       - Has entry point
       - Has dependencies
       - No service config
    
    3. LIBRARY:
       - Has dependencies
       - No entry point or setup.py/pyproject.toml with [build-system]
    
    4. SCRIPT:
       - Single Python file or few files
       - No dependency declaration
    """
    # Rule-based (no heuristics)
    # Explicit markers only
```

---

### **4. Environment Checker** (`pyready/env_checker/`)

**Purpose:** Validate Python environment setup

**Files:**
- `orchestrator.py` - Coordinates all checks
- `python_version.py` - Python version validation
- `venv_detector.py` - Virtual environment detection
- `dependency_checker.py` - Dependency installation check
- `env_vars_checker.py` - Environment variable validation
- `expectations.py` - Define expected state

**Check Architecture:**
```python
class EnvironmentCheck:
    """Base class for all checks"""
    
    def check(self, context: CheckContext) -> CheckResult:
        """
        Returns:
        - status: PASS, WARN, FAIL
        - message: Human-readable explanation
        - details: Structured diagnostic info
        - fix_suggestion: Optional remediation command
        """
```

**Python Version Check:**
```python
def check_python_version(path: Path) -> CheckResult:
    """
    1. Find version requirement (pyproject.toml, .python-version, etc.)
    2. Get current Python version (sys.version_info)
    3. Compare using packaging.specifiers
    4. Return PASS/FAIL with specific version info
    """
    # Deterministic: same project = same result
    # No network calls
    # Explicit version sources only
```

---

### **5. Run Detection** (`pyready/run_detection/`)

**Purpose:** Detect how to run the project

**Files:**
- `detector.py` - Run command detection
- `models.py` - Run command models

**Detection Strategy (Deterministic):**
```python
def detect_run_command(path: Path, capabilities: CapabilityReport) -> RunCommand:
    """
    Priority (explicit → implicit):
    
    1. Explicit:
       - pyproject.toml [tool.poetry.scripts]
       - setup.py entry_points
       - Procfile
    
    2. Pattern-based:
       - FastAPI: uvicorn app.main:app
       - Flask: flask run
       - Django: python manage.py runserver
       - Streamlit: streamlit run app.py
       - __main__.py: python -m <package>
    
    3. Fallback:
       - python <entry_file>
    """
    # AST parsing for imports (static)
    # File pattern matching
    # No execution
```

---

### **6. Analysis** (`pyready/analysis/`)

**Purpose:** Static code analysis

**Files:**
- `ast_parser.py` - Parse Python files without importing
- `dependency_graph.py` - Build import dependency graph

**AST Parsing:**
```python
def parse_imports(file: Path) -> List[ImportInfo]:
    """
    Uses ast.parse() to extract:
    - import statements
    - from ... import statements
    - Function definitions
    - Class definitions
    
    No code execution!
    """
    with open(file) as f:
        tree = ast.parse(f.read(), filename=str(file))
    # Walk AST tree
    # Collect import nodes
    # Return structured data
```

---

### **7. Policy Engine** (`pyready/policy/`)

**Purpose:** Evaluate policies against diffs

**Files:**
- `engine.py` - Policy evaluation logic
- `explain.py` - Deterministic explanation generator

**Policy Evaluation:**
```python
def evaluate_policy(policy: Policy, diff: DiffReport) -> PolicyResult:
    """
    For each rule:
    1. Match diff items against rule conditions (AND logic)
    2. Check wildcards (fnmatch)
    3. Extract values (handles "Status: PASS" or "PASS")
    4. Aggregate results (FAIL > WARN > PASS)
    5. Generate deterministic explanation
    
    Guarantees:
    - Same policy + same diff = same result (always)
    - Same explanation text (character-for-character)
    - Auditable (shows why each rule matched/didn't)
    """
```

**Explanation Generation (Deterministic):**
```python
def generate_explanation(rule: PolicyRule, matched: bool, diff_item: DiffItem) -> str:
    """
    Template-based explanation (no AI):
    
    - If matched:
      "This rule matched because changes were detected in the '<section>'
       section where the '<key>' field changed from [<from>] to [<to>]."
    
    - If not matched:
      "This rule was evaluated but did not match because no '<key>' field
       changed to [<to>] in the '<section>' section."
    
    100% reproducible - same inputs = identical text
    """
```

---

### **8. Reporting** (`pyready/reporting/`)

**Purpose:** Generate and export reports

**Files:**
- `generator.py` - Report generation
- `diff.py` - Diff computation

**Report Generation:**
```python
def generate_report(detection: ProjectDetection, 
                    checks: List[CheckResult],
                    recommendations: List[Recommendation]) -> Report:
    """
    Combines:
    - Capabilities (from detection)
    - Environment checks (from validators)
    - Recommendations (from recommendation engine)
    - Run command (from run detector)
    
    Returns Pydantic model (validated)
    Serializes to JSON/Markdown
    """
```

**Diff Computation:**
```python
def compute_diff(old_report: Report, new_report: Report) -> DiffReport:
    """
    Compares:
    1. Capabilities (added, removed, changed)
    2. Checks (status changes, message changes)
    3. Intent (classification changes)
    4. Run command (command changes)
    5. Recommendations (new/removed suggestions)
    
    Returns structured diff items:
    - section: "capabilities", "checks", etc.
    - key: specific field name
    - change_type: "added", "removed", "changed"
    - before/after values
    
    Stable ordering (alphabetical by section → key)
    """
```

---

### **9. Schemas** (`pyready/schemas/`)

**Purpose:** Data validation and contracts

**Files:**
- `capability_schema.py` - Capability models
- `report_schema.py` - Report models
- `diff_schema.py` - Diff models
- `policy_schema.py` - Policy models
- `policy_explain_schema.py` - Policy explanation models
- `env_schema.py` - Environment check models
- `repo_schema.py` - Repository scan models

**Schema Design Pattern:**
```python
from pydantic import BaseModel, Field

class CapabilityReport(BaseModel):
    """
    Immutable data model with validation.
    
    Benefits:
    - Type safety (mypy compatible)
    - Automatic JSON serialization
    - Input validation
    - Documentation via Field()
    """
    has_python_files: bool
    has_python_files_evidence: List[str] = Field(default_factory=list)
    has_dependency_declaration: bool
    # ...
    
    class Config:
        frozen = True  # Immutable (no accidental mutation)
```

---

## 🔄 Data Flow

### **Check Command Flow**

```
User runs: pyready check .
    ↓
1. CLI Layer (check.py)
   - Parse arguments
   - Validate path exists
    ↓
2. Project Detection (detector.py)
   - Scan filesystem
   - Detect project type
   - Collect capabilities
   - Classify intent
    ↓
3. Environment Validation (orchestrator.py)
   - Check Python version
   - Check virtual environment
   - Check dependencies
   - Check env variables
    ↓
4. Run Detection (detector.py)
   - Detect entry points
   - Find run patterns
   - Generate run command
    ↓
5. Recommendation Engine (engine.py)
   - Analyze check results
   - Generate suggestions
   - Provide fix commands
    ↓
6. Report Generation (generator.py)
   - Combine all data
   - Validate schema
   - Serialize to JSON/Markdown
    ↓
7. Output
   - Terminal (Rich formatting)
   - File (JSON/Markdown)
   - Exit code 0
```

### **Diff Command Flow**

```
User runs: pyready diff old.json new.json --policy policy.yml
    ↓
1. CLI Layer (diff.py)
   - Parse arguments
   - Load reports (JSON)
   - Load policy (YAML/JSON)
    ↓
2. Diff Computation (diff.py)
   - Compare capabilities
   - Compare checks
   - Compare intent
   - Compare run commands
   - Generate diff items
    ↓
3. Policy Evaluation (engine.py)
   - Load policy rules
   - Match rules against diff items
   - Evaluate conditions (AND logic)
   - Aggregate results (FAIL > WARN > PASS)
    ↓
4. Explanation Generation (explain.py)
   - Generate deterministic explanation
   - For each rule: why matched/not matched
   - Include triggered diff items
    ↓
5. Output
   - Terminal (diff summary + policy result)
   - File (JSON/Markdown)
   - Exit code: 0 (PASS), 1 (WARN), 2 (FAIL)
```

---

## 📊 Schema Design

### **Report Schema Hierarchy**

```
Report
├── metadata (timestamp, version, path)
├── detection
│   ├── project_type (poetry, pip_venv, etc.)
│   ├── capabilities
│   │   ├── has_python_files (bool + evidence list)
│   │   ├── has_dependency_declaration (bool + evidence list)
│   │   ├── has_isolated_environment (bool + evidence list)
│   │   ├── has_reproducible_environment (bool + evidence list)
│   │   └── has_entry_point (bool + evidence list)
│   └── intent (script, library, application, service)
├── checks (list of CheckResult)
│   ├── name (e.g., "Python Version")
│   ├── status (PASS, WARN, FAIL)
│   ├── message (human-readable)
│   ├── details (structured diagnostic info)
│   └── fix_suggestion (optional command)
├── recommendations (list of Recommendation)
│   ├── title
│   ├── description
│   ├── evidence
│   └── example
└── run_command
    ├── command (e.g., "poetry run pyready")
    ├── evidence (list of detection sources)
    └── detection_basis ("explicit", "pattern-based", "fallback")
```

### **Diff Schema**

```
DiffReport
├── old_timestamp
├── new_timestamp
├── total_changes (int)
└── changes (list of DiffItem)
    ├── section ("capabilities", "checks", "intent", "run_command")
    ├── key (specific field name)
    ├── change_type ("added", "removed", "changed")
    ├── before (optional, any type)
    └── after (optional, any type)
```

### **Policy Schema**

```
Policy
├── version (int, must be 1)
└── rules (list of PolicyRule)
    ├── id (unique identifier)
    ├── description (human-readable)
    ├── when (conditions, all ANDed)
    │   ├── section (optional)
    │   ├── key (optional, supports wildcards)
    │   ├── field (optional)
    │   ├── change_type (optional)
    │   ├── from (optional list of values)
    │   └── to (optional list of values)
    ├── action ("FAIL" or "WARN")
    └── enabled (bool)
```

---

## 🔒 Determinism Guarantees

### **How PyReady Ensures Determinism**

1. **No External Dependencies in Core**
   - No API calls
   - No network requests
   - No database queries
   - Filesystem only (read-only)

2. **Stable Sorting**
   ```python
   # Always sort results alphabetically
   files = sorted(Path(path).glob("*.py"))
   
   # Stable dict ordering (Python 3.7+)
   capabilities = {
       "has_python_files": ...,
       "has_dependency_declaration": ...,
       # ... (always same order)
   }
   ```

3. **No Timestamps in Comparisons**
   ```python
   # ❌ BAD: Non-deterministic
   report.created_at = datetime.now()
   
   # ✅ GOOD: Timestamp for metadata only
   report.metadata.timestamp = datetime.now(timezone.utc).isoformat()
   # Never used in comparisons or logic
   ```

4. **Explicit Value Extraction**
   ```python
   # Handles "Status: PASS" or "PASS"
   def extract_status(value: str) -> str:
       if ":" in value:
           return value.split(":", 1)[1].strip()
       return value.strip()
   ```

5. **Pydantic Validation**
   - Catches type mismatches
   - Enforces schema contracts
   - Prevents accidental mutations (frozen=True)

6. **Pure Functions**
   ```python
   def detect_capabilities(path: Path) -> CapabilityReport:
       """
       Same path → same result (always)
       No side effects
       No global state
       """
   ```

---

## 🔌 Extension Points

### **Adding New Project Types**

```python
# pyready/project_detection/detector.py

def detect_project_type(path: Path) -> ProjectType:
    # Add new detection logic
    if (path / "new_file.yml").exists():
        return ProjectType.NEW_TYPE
    
    # Existing logic...
```

### **Adding New Checks**

```python
# pyready/env_checker/new_checker.py

class NewCheck(EnvironmentCheck):
    def check(self, context: CheckContext) -> CheckResult:
        # Implement check logic
        if condition:
            return CheckResult(
                name="New Check",
                status=CheckStatus.PASS,
                message="Check passed",
            )
        else:
            return CheckResult(
                name="New Check",
                status=CheckStatus.FAIL,
                message="Check failed",
                fix_suggestion="Run: fix-command",
            )
```

### **Adding New Policy Conditions**

```python
# pyready/policy/engine.py

def match_rule(rule: PolicyRule, diff_item: DiffItem) -> bool:
    # Add new condition matching logic
    if rule.when.new_condition:
        # Evaluate new condition
        pass
    
    # Existing logic...
```

---

## ⚡ Performance Considerations

### **Optimization Strategies**

1. **Lazy Loading**
   ```python
   # Only parse files when needed
   def get_imports(self) -> List[ImportInfo]:
       if self._imports is None:
           self._imports = parse_imports(self.path)
       return self._imports
   ```

2. **File System Caching**
   ```python
   # Cache file existence checks within single run
   _cache: Dict[Path, bool] = {}
   
   def file_exists(path: Path) -> bool:
       if path not in _cache:
           _cache[path] = path.exists()
       return _cache[path]
   ```

3. **Early Exit**
   ```python
   # Stop checking once project type found
   for detector in DETECTORS:
       if result := detector(path):
           return result
   ```

4. **Minimal File Reading**
   ```python
   # Only read file headers for project type detection
   def has_poetry_section(path: Path) -> bool:
       with open(path / "pyproject.toml") as f:
           for line in f:
               if "[tool.poetry]" in line:
                   return True
       return False
   ```

### **Performance Targets**

| Operation | Target | Current |
|-----------|--------|---------|
| Capability Detection | <200ms | 50-200ms |
| Environment Checks | <500ms | 100-500ms |
| Report Generation | <100ms | <100ms |
| Diff Computation | <50ms | <50ms |
| Policy Evaluation | <10ms | <10ms |
| Full Pipeline | <1s | 300ms-1s |

---

## 🧪 Testing Strategy

### **Test Pyramid**

```
        /\
       /  \
      / E2E \ (10% - Full CLI commands)
     /______\
    /        \
   / Integ   \ (30% - Module interactions)
  /  Tests    \
 /____________\
/              \
/ Unit Tests    \ (60% - Pure functions)
/________________\
```

### **Unit Tests**

```python
# Test pure functions
def test_detect_capabilities():
    # Given: Project with pyproject.toml
    path = tmp_path / "project"
    (path / "pyproject.toml").touch()
    
    # When: Detect capabilities
    result = detect_capabilities(path)
    
    # Then: Should find dependency declaration
    assert result.has_dependency_declaration is True
    assert "pyproject.toml" in result.has_dependency_declaration_evidence
```

### **Integration Tests**

```python
# Test module interactions
def test_check_command_pipeline():
    # Given: Complete project
    project = create_test_project()
    
    # When: Run check command
    result = check_command(project.path)
    
    # Then: Should generate valid report
    assert result.detection.project_type == "poetry"
    assert len(result.checks) == 4
    assert result.run_command.command == "poetry run python app.py"
```

### **E2E Tests**

```python
# Test CLI commands
def test_cli_check(cli_runner):
    # Given: Real project
    result = cli_runner.invoke(app, ["check", "test-project/"])
    
    # Then: Should exit 0 and show output
    assert result.exit_code == 0
    assert "Project type detected: poetry" in result.output
```

### **Determinism Tests**

```python
# Test reproducibility
def test_deterministic_report_generation():
    # Given: Same project
    path = Path("test-project/")
    
    # When: Generate report twice
    report1 = generate_report(path)
    report2 = generate_report(path)
    
    # Then: Should be identical (except timestamp)
    assert report1.detection == report2.detection
    assert report1.checks == report2.checks
    assert report1.run_command == report2.run_command
```

---

## 📚 Further Reading

- [POLICY_GUIDE.md](POLICY_GUIDE.md) - Comprehensive policy system guide
- [README.md](README.md) - User-facing documentation
- [CONTRIBUTING.md](CONTRIBUTING.md) - Development guidelines

---

## 🙏 Architecture Credits

Designed and implemented by Aditya Mallela  
Inspired by principles from:
- Clean Architecture (Robert C. Martin)
- Domain-Driven Design (Eric Evans)
- Functional Core, Imperative Shell (Gary Bernhardt)

---

**Last Updated:** January 6, 2026  
**Version:** 0.2.0
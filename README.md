# 🚀 PyReady

**"Is your Python project ready?"**

**Python project environment checker and governance tool with deterministic analysis**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production-success.svg)](https://github.com)
[![Poetry](https://img.shields.io/badge/Managed%20by-Poetry-blue.svg)](https://python-poetry.org/)
[![Typer](https://img.shields.io/badge/CLI-Typer-purple.svg)](https://typer.tiangolo.com/)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Key Principles](#-key-principles)
- [Features](#-features)
- [What Makes PyReady Different](#-what-makes-pyready-different)
- [Installation](#-installation)
- [Quick Start](#-quick-start)
- [CLI Commands](#-cli-commands)
- [Policy System](#-policy-system)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Use Cases](#-use-cases)
- [CI/CD Integration](#-cicd-integration)
- [Troubleshooting](#-troubleshooting)
- [Performance](#-performance)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

PyReady is a **deterministic project environment analysis and governance tool** for Python projects. It performs static, read-only analysis to detect capabilities, validate setup, generate reports, track changes over time, and enforce team-defined standards through declarative policies.

**Built for:** Development teams requiring reproducible, auditable environment validation  
**Use Cases:** CI/CD gating, compliance audits, developer onboarding, dependency governance  
**Core Guarantee:** Identical inputs → Identical outputs (character-for-character)

---

## 🔑 Key Principles

PyReady is built around strict guarantees:

- **✅ Deterministic** — No heuristics, no probabilistic logic, same input = same output always
- **✅ Static** — No code execution, no imports, no runtime inspection
- **✅ Read-only** — Never modifies project files
- **✅ Explainable** — Every policy decision is traceable with deterministic explanations
- **✅ Operator-controlled** — Standards come from policy files, not the tool
- **✅ CI/CD-safe** — Exit codes (0/1/2) are stable and meaningful

Optional AI features exist via Groq, but **never influence core behavior**.

---

## ✨ Features

### **Static Environment Analysis**
- 🔍 **Capability Detection** - Detects Python files, dependency declarations, virtual environments, lock files, entry points
- 📊 **Evidence-Based** - Records filesystem evidence for every capability detected
- 🎯 **Project Intent Classification** - Classifies as script, library, application, or service using explicit markers

### **Environment Validation**
- ✅ **Deterministic Checks** - Python version compatibility, venv presence, dependency status
- 🎨 **Rich Terminal UI** - Color-coded status symbols (✔/✖/⚠) with detailed messages
- 📝 **Advisory Recommendations** - Evidence-based suggestions, never enforced

### **Report Generation & Export**
- 📄 **JSON Export** - Machine-readable reports for CI/CD pipelines
- 📖 **Markdown Export** - Human-readable reports for documentation
- 🔄 **Complete Serialization** - Capabilities, checks, recommendations, run commands

### **Environment Diffing**
- 🔀 **Precise Change Detection** - Compares two reports to show exactly what changed
- 📋 **Structured Diff Items** - Tracks section, key, change_type, before/after values
- 🎯 **Stable Ordering** - Deterministic diff output for version control

### **Policy Enforcement System**
- 📜 **Declarative Policies** - YAML/JSON policy files with rule-based matching
- ⚖️ **Deterministic Evaluation** - Pure pattern matching with AND logic
- 🚦 **Exit Codes** - PASS (0), WARN (1), FAIL (2) for automated gating
- 🔍 **Wildcard Support** - Unix-style patterns (`*_status`, `checks.*`)

### **Policy Explanation & Audit Trail**
- 📖 **Deterministic Explanations** - Template-based, no AI, character-for-character reproducible
- 🔬 **Complete Traceability** - Shows why every rule matched or didn't match
- 📊 **Export to JSON/Markdown** - Audit-ready explanation reports

### **Optional AI Features (Groq)**
- 💬 **Natural Language Q&A** - `explain` command answers questions about projects
- 📝 **Run Command Explanations** - `--explain` flag adds human-readable context
- 🔒 **Isolated from Core** - AI failures never break deterministic functionality

---

## 🌟 What Makes PyReady Different

| Feature | PyReady | Traditional Linters | CI/CD Scripts |
|---------|-----------|-------------------|---------------|
| **Determinism** | ✅ Guaranteed | ⚠️ Version-dependent | ❌ Environment-dependent |
| **Policy Audit Trail** | ✅ Exportable explanations | ❌ No traceability | ❌ Manual logs only |
| **Change Governance** | ✅ Diff + Policy system | ❌ File-level only | ⚠️ Custom scripting |
| **Zero Code Execution** | ✅ Static analysis only | ⚠️ May import code | ⚠️ Often executes tests |
| **Exit Code Stability** | ✅ 0/1/2 always meaningful | ⚠️ Tool-dependent | ⚠️ Script-dependent |
| **Compliance Ready** | ✅ Reproducible outputs | ❌ Heuristic-based | ❌ Custom validation |

**Key Differentiator:** PyReady's policy explanations are 100% deterministic - same inputs produce identical explanations, enabling audit compliance and regression testing that traditional tools cannot provide.

---

## 📦 Installation

### **Prerequisites**
- Python 3.9+
- Poetry (recommended) or pip
- Git (for version control)

### **Option 1: Install via pip (when published)**
```bash
pip install pyready
```

### **Option 2: Install via Poetry**
```bash
poetry add --group dev pyready
```

### **Option 3: Install from Source**
```bash
# Clone repository
git clone https://github.com/AdityaMallela041/PyReady.git
cd PyReady

# Install with Poetry
poetry install

# Or install with pip
pip install -e .
```

### **Verify Installation**
```bash
pyready --help
```

Expected output:
```
Usage: pyready [OPTIONS] COMMAND [ARGS]...

  PyReady CLI - Project environment checker and assistant

Commands:
  check    Check the development environment for a project
  diff     Compare two PyReady reports
  explain  Answer questions about the project
```

---

## 🚀 Quick Start

### **1. Analyze Your Project**
```bash
# Check current directory
pyready check .

# Check specific project
pyready check /path/to/project
```

Output Example:
```
🔍 Project type detected: poetry
Evidence:
 -  pyproject.toml
 -  [tool.poetry] section found

📦 Project capabilities:
 ✔ Python files detected
 ✔ Dependency declaration found
 ✔ Isolated environment (venv)
 ✔ Reproducible environment (lock file)
 ✔ Entry point detectable

🚀 Project intent: application

✔ Python Version: Python 3.11.8 found ✓
✔ Virtual Environment: Active virtual environment detected
✔ Dependencies: All dependencies installed
```

### **2. Export Report**
```bash
# JSON format (for CI/CD)
pyready check . --output report.json

# Markdown format (for documentation)
pyready check . --output report.md
```

### **3. Compare Environments**
```bash
# Generate baseline
pyready check . --output baseline.json

# Make changes to project (modify dependencies, etc.)

# Generate new report
pyready check . --output current.json

# Compare
pyready diff baseline.json current.json
```

Diff Output Example:
```
📊 Diff Summary
From: 2026-01-05T12:00:00
To: 2026-01-05T14:30:00

Total changes: 3

📦 Capability Changes
 + has_reproducible_environment
   After: true

✓ Check Changes
 ~ Python Version
   Before: 3.9.0
   After: 3.11.8
```

### **4. Enforce Policy**
```bash
# Create policy file
cat > .pyready-policy.yml << EOF
version: 1
rules:
  - id: no-python-downgrade
    description: "Prevent Python version downgrade"
    when:
      section: checks
      field: status
      change_type: changed
      to: ["FAIL"]
    action: FAIL
    enabled: true
EOF

# Evaluate policy
pyready diff baseline.json current.json --policy .pyready-policy.yml --explain-policy
```

---

## 📖 CLI Commands

### `pyready check [PATH]`
Analyzes a Python project directory.

**Arguments:**
- `[PATH]` - Project directory (defaults to current directory)

**Options:**
- `--output, -o <FILE>` - Export report to JSON or Markdown
- `--explain, -e` - Include AI-assisted explanations (requires GROQ_API_KEY)

**Exit Code:** Always 0 (analysis only, no enforcement)

**Example:**
```bash
# Basic check
pyready check .

# With AI explanations
pyready check . --explain

# Export to JSON
pyready check . --output report.json
```

### `pyready diff <OLD> <NEW>`
Compares two PyReady reports.

**Arguments:**
- `<OLD>` - Baseline JSON report
- `<NEW>` - Current JSON report

**Options:**
- `--output, -o <FILE>` - Export diff to JSON or Markdown
- `--policy, -p <FILE>` - Policy file (.yml, .yaml, .json)
- `--explain-policy` - Show detailed policy explanation (requires --policy)

**Exit Codes:**
- `0` - PASS (no violations or no policy)
- `1` - WARN (warnings detected)
- `2` - FAIL (failures detected or error)

**Example:**
```bash
# Basic diff
pyready diff baseline.json current.json

# With policy enforcement
pyready diff baseline.json current.json --policy .pyready-policy.yml

# With policy explanation
pyready diff baseline.json current.json \
  --policy .pyready-policy.yml \
  --explain-policy
```

### `pyready explain <QUESTION>`
Answer questions about the project using analysis.

**Arguments:**
- `<QUESTION>` - Question to answer

**Options:**
- `--path, -p <PATH>` - Project directory (defaults to current directory)

**Requirements:** GROQ_API_KEY environment variable

**Supported Questions:**
- "Why is [package] required?"
- "What runs when I start the project?"
- "What breaks if I remove [package]?"
- "Where is [module] used?"

**Example:**
```bash
# Ask about dependencies
pyready explain "Why is FastAPI required?"

# Ask about run commands
pyready explain "What runs when I start the project?"
```

---

## 🛡️ Policy System

### **Why Policies?**
PyReady detects changes, but you define what changes are acceptable. Policies enable:

✅ Preventing Python version downgrades  
✅ Blocking removal of critical dependencies  
✅ Enforcing virtual environment usage  
✅ Gating CI/CD pipelines on environment health

### **Policy File Format**
Policies are YAML or JSON files:

```yaml
version: 1

rules:
  - id: no-venv-removal
    description: "Virtual environment must not be removed"
    when:
      section: capabilities
      key: has_isolated_environment
      change_type: changed
      from: ["true"]
      to: ["false"]
    action: FAIL
    enabled: true

  - id: warn-on-new-failures
    description: "Warn if any check starts failing"
    when:
      section: checks
      field: status
      to: ["FAIL"]
    action: WARN
    enabled: true
```

### **Rule Anatomy**

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique rule identifier | `no-python-downgrade` |
| `description` | Human-readable explanation | `"Prevent Python version downgrade"` |
| `when.section` | Section to match | `capabilities`, `checks`, `intent` |
| `when.key` | Specific key (supports wildcards) | `has_*`, `Python_*` |
| `when.change_type` | Change type | `added`, `removed`, `changed` |
| `when.field` | Field within key | `status` (for checks) |
| `when.from` | Before values | `["PASS", "WARN"]` |
| `when.to` | After values | `["FAIL"]` |
| `action` | Action when matched | `FAIL` or `WARN` |
| `enabled` | Whether rule is active | `true` or `false` |

### **Matching Logic**
- All conditions in `when` are ANDed together
- Wildcard matching uses fnmatch (e.g., `*_status`, `checks.*`)
- Value extraction handles both "Status: PASS" and "PASS" formats
- Rules are evaluated independently (multiple rules can match same change)
- Final status = highest severity: FAIL > WARN > PASS

### **Policy Explanation (Deterministic)**
PyReady's policy explanations are 100% deterministic:

```bash
pyready diff baseline.json current.json \
  --policy .pyready-policy.yml \
  --explain-policy
```

Output:
```
📖 Policy Explanation
  2 of 3 rules matched

Rule: no-venv-removal
Status: ❌ MATCHED (FAIL)
Reason:
  This rule matched because changes were detected in the 'capabilities'
  section where the 'has_isolated_environment' field changed from [true] to [false].
  
  Triggered by: capabilities.has_isolated_environment

Rule: warn-on-new-failures
Status: ✓ NOT MATCHED
Reason:
  This rule was evaluated but did not match because no 'status' field
  changed to [FAIL] in the 'checks' section.
```

**Key Feature:** Same policy + same diff = identical explanation text (character-for-character). This enables:
- Audit compliance (reproducible decisions)
- Regression testing (compare explanation strings)
- CI/CD caching (deterministic outputs)

---

## 📁 Project Structure

```
pyready/
├── pyready/
│   ├── cli/
│   │   ├── main.py              # CLI entry point
│   │   ├── check.py             # Check command
│   │   ├── diff.py              # Diff command
│   │   └── explain.py           # Q&A command
│   ├── policy/
│   │   ├── engine.py            # Policy evaluation
│   │   └── explain.py           # Deterministic explanations
│   ├── project_detection/       # Project type detection
│   ├── env_checker/             # Environment validation
│   ├── run_detection/           # Run command detection
│   ├── schemas/
│   │   ├── capability_schema.py
│   │   ├── policy_schema.py
│   │   ├── policy_explain_schema.py
│   │   ├── report_schema.py
│   │   ├── diff_schema.py
│   │   └── env_schema.py
│   └── reporting/               # Export functions
├── pyproject.toml               # Poetry configuration
├── README.md                    # This file
└── LICENSE                      # MIT License
```

---

## ⚙️ Configuration

### **Environment Variables**
Create a `.env` file for optional features:

```bash
# Optional: Groq API for natural language features
GROQ_API_KEY=gsk_your_groq_api_key_here
```

**Get Groq API Key:**
1. Visit [console.groq.com](https://console.groq.com)
2. Sign up (free tier available)
3. Generate API key
4. Add to `.env` file

**Note:** Groq is only used for:
- `pyready explain` command (Q&A)
- `pyready check --explain` flag (run command explanations)

Core features work without Groq (capability detection, checks, policies, diffs).

---

## 💼 Use Cases

### **1. Developer Onboarding**
**Problem:** New developers waste hours figuring out project setup  
**Solution:** `pyready check .` shows exactly what's missing

```bash
# New developer runs this first
pyready check /path/to/project

# Output shows:
# ✔ Python 3.11 found
# ✖ Virtual environment missing
# ✖ Dependencies not installed
# → poetry install
```

### **2. CI/CD Environment Gating**
**Problem:** Code merges that break environment setup  
**Solution:** Policy enforcement blocks bad PRs

```yaml
# .github/workflows/environment-gate.yml
- name: Environment Policy Check
  run: |
    pyready diff baseline.json pr.json \
      --policy .pyready-policy.yml
  # Exits with code 2 (FAIL) if policy violated → blocks merge
```

### **3. Dependency Governance**
**Problem:** Unreviewed dependency changes slip through  
**Solution:** Track and audit all dependency changes

```bash
# Before release
pyready check . --output pre-release.json

# After release
pyready check . --output post-release.json

# Audit what changed
pyready diff pre-release.json post-release.json --output CHANGELOG.md
```

### **4. Compliance Audits**
**Problem:** Need to prove environment decisions were deterministic  
**Solution:** Exportable policy explanations

```bash
# Generate audit trail
pyready diff Q3-baseline.json Q4-current.json \
  --policy security-policy.yml \
  --explain-policy \
  --output audit-report.json

# Report shows:
# - What changed
# - Which rules triggered
# - Why each decision was made (deterministic)
```

---

## 🔄 CI/CD Integration

### **GitHub Actions**
```yaml
name: Environment Policy Gate

on:
  pull_request:
    branches: [main]

jobs:
  policy-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Need history for base commit

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install PyReady
        run: pip install pyready

      - name: Generate baseline report
        run: |
          git checkout ${{ github.event.pull_request.base.sha }}
          pyready check . --output /tmp/baseline.json

      - name: Generate PR report
        run: |
          git checkout ${{ github.event.pull_request.head.sha }}
          pyready check . --output /tmp/pr.json

      - name: Evaluate policy
        run: |
          pyready diff /tmp/baseline.json /tmp/pr.json \
            --policy .pyready-policy.yml \
            --explain-policy

      # Exit code 0 = PASS, 1 = WARN (continue), 2 = FAIL (blocks merge)
```

### **GitLab CI**
```yaml
environment-policy:
  stage: test
  script:
    - pip install pyready
    - git checkout $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - pyready check . --output baseline.json
    - git checkout $CI_COMMIT_SHA
    - pyready check . --output current.json
    - pyready diff baseline.json current.json --policy .pyready-policy.yml
  rules:
    - if: $CI_PIPELINE_SOURCE == 'merge_request_event'
```

### **Pre-commit Hook**
```bash
# .git/hooks/pre-commit
#!/bin/bash

# Generate current report
pyready check . --output /tmp/current.json

# Compare with baseline (if exists)
if [ -f .pyready-baseline.json ]; then
  pyready diff .pyready-baseline.json /tmp/current.json \
    --policy .pyready-policy.yml || exit 1
fi
```

---

## 🐛 Troubleshooting

### **Common Issues**

#### **1. "Command not found: pyready"**
**Cause:** Not installed or not in PATH  
**Solution:**
```bash
# Verify installation
pip list | grep pyready

# Or check Poetry
poetry show pyready

# Reinstall
pip install --force-reinstall pyready
```

#### **2. "Policy file not found"**
**Cause:** Incorrect path or filename  
**Solution:**
```bash
# Check file exists
ls -la .pyready-policy.yml

# Use absolute path
pyready diff old.json new.json --policy /full/path/to/policy.yml
```

#### **3. "GROQ_API_KEY not set" (explain command)**
**Cause:** Groq API key missing, but command requires it  
**Solution:**
```bash
# Create .env file
echo "GROQ_API_KEY=gsk_your_key_here" > .env

# Or export directly
export GROQ_API_KEY="gsk_your_key_here"
```

**Note:** This only affects `explain` command. Other commands work without Groq.

#### **4. "Natural language explanations unavailable"**
**Cause:** Groq unavailable but `--explain` flag used  
**Behavior:** Command continues, just shows: "ℹ️ Natural language explanations unavailable"

This is normal: Core functionality (detection, checks, reports) still works perfectly.

#### **5. Policy always returns PASS (no violations)**
**Cause:** Rule conditions don't match diff items  
**Solution:**
```bash
# Debug with --explain-policy
pyready diff old.json new.json \
  --policy .pyready-policy.yml \
  --explain-policy

# Check "Reason" field for each rule to see why it didn't match
```

#### **6. "Invalid policy file format"**
**Cause:** YAML syntax error  
**Solution:**
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('.pyready-policy.yml'))"

# Common issues:
# - Missing quotes around values with colons
# - Incorrect indentation (use 2 spaces)
# - Missing 'version: 1' at top
```

### **Debug Mode**
Enable verbose output:
```bash
# See what PyReady detects
pyready check . -vvv

# Check policy matching logic
pyready diff old.json new.json \
  --policy .pyready-policy.yml \
  --explain-policy -vvv
```

---

## 📊 Performance

| Operation | Time | Notes |
|-----------|------|-------|
| Capability Detection | 50-200ms | Depends on project size |
| Environment Checks | 100-500ms | Includes Python version, venv checks |
| Report Generation | <100ms | Pure serialization |
| Diff Computation | <50ms | Compares two JSON reports |
| Policy Evaluation | <10ms | Deterministic pattern matching |
| Policy Explanation | <20ms | Template-based, no AI |
| Full Check Pipeline | 300ms-1s | End-to-end for medium project |

**Determinism Overhead:** Zero - deterministic operations are often faster than heuristic alternatives.

---

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

### **Accepted Contributions**
✅ Bug fixes  
✅ Documentation improvements  
✅ Test coverage expansion  
✅ Compatibility updates (new Python versions, OS)  
✅ Performance optimizations (maintaining determinism)

### **Declined Contributions**
❌ Auto-remediation features (conflicts with read-only principle)  
❌ Heuristic logic (conflicts with determinism)  
❌ Runtime code execution (conflicts with static analysis)  
❌ Expanding scope beyond governance

**Why the boundaries?** Preserving determinism, predictability, and operator trust.

### **Development Setup**
```bash
# Clone repo
git clone https://github.com/AdityaMallela041/PyReady.git
cd PyReady

# Install with dev dependencies
poetry install

# Run tests
poetry run pytest

# Check code style
poetry run black --check .
poetry run mypy .
```

### **Commit Message Format**
Use conventional commits:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Test updates
- `refactor:` Code refactoring

---

## 📝 Changelog

### **v0.1.0 (Phase 14.5 - Current)**
- ✨ Deterministic policy explanation system
- ✨ Groq hardening with graceful fallback
- ✨ python-dotenv support for .env files
- ✨ Policy diff with --explain-policy flag
- ✅ Production-ready status
- 🔒 100% audit compliance (deterministic explanations)
- 📦 All schemas frozen for stability

---

## 📄 License

This project is licensed under the MIT License.

---

## 👥 Authors

**Aditya Mallela**  
Computer Science Student (AI & ML)  

📧 Contact: [adityamallela041@gmail.com]  
🌐 GitHub: [@AdityaMallela041](https://github.com/AdityaMallela041)

---

## 🙏 Acknowledgments

- **Typer** - Beautiful CLI framework
- **Rich** - Terminal UI library
- **Pydantic** - Data validation
- **Groq** - Optional LLM inference
- **Poetry** - Dependency management

---

## 📞 Support

For issues, questions, or suggestions:

- 🐛 **GitHub Issues:** [Create Issue](https://github.com/AdityaMallela041/PyReady/issues)
- 📖 **Documentation:** See ARCHITECTURE.md and POLICY_GUIDE.md
- 💬 **Discussions:** [GitHub Discussions](https://github.com/AdityaMallela041/PyReady/discussions)

---

<div align="center">


⭐ **Star this repo if you value reproducible environment validation!**

🚀 **Production-ready with audit-grade policy explanations!** 📋

</div>
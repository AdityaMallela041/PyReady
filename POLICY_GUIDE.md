# 📜 PyReady Policy System Guide

**Complete Guide to Declarative Environment Governance**

Version: 0.2.0  
Last Updated: January 6, 2026

---

## 📋 Table of Contents

- [Introduction](#introduction)
- [Why Policies?](#why-policies)
- [Quick Start](#quick-start)
- [Policy File Format](#policy-file-format)
- [Rule Anatomy](#rule-anatomy)
- [Matching Logic](#matching-logic)
- [Examples](#examples)
- [Advanced Patterns](#advanced-patterns)
- [Policy Explanations](#policy-explanations)
- [Best Practices](#best-practices)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)

---

## 🎯 Introduction

PyReady's policy system allows you to **define governance rules** that automatically evaluate environment changes. Instead of manually reviewing every change, policies encode your team's standards and enforce them deterministically.

### **Core Concepts**

- **Declarative:** Rules are written in YAML/JSON, not code
- **Deterministic:** Same inputs always produce same results
- **Auditable:** Every decision is explained and traceable
- **Composable:** Multiple rules can be combined
- **Exit-code driven:** CI/CD pipelines use exit codes (0/1/2) for gating

---

## 💡 Why Policies?

### **Problem: Manual Environment Reviews**

Without policies:
```bash
# Developer opens PR
git diff main...feature-branch

# Reviewer manually checks:
# - Did Python version change?
# - Were dependencies added/removed?
# - Is virtual environment still configured?
# - Did environment variables change?

# 🚨 Easy to miss issues!
```

### **Solution: Automated Policy Enforcement**

With policies:
```bash
# CI/CD automatically runs:
pyready diff baseline.json pr.json --policy .pyready-policy.yml

# Exit code:
# 0 = PASS (merge allowed)
# 1 = WARN (review recommended)
# 2 = FAIL (blocks merge)

# ✅ Zero human errors!
```

---

## 🚀 Quick Start

### **1. Create Your First Policy**

```yaml
# .pyready-policy.yml
version: 1

rules:
  - id: no-python-downgrade
    description: "Prevent Python version downgrades"
    when:
      section: checks
      key: Python_Version
      field: status
      change_type: changed
      to: ["FAIL"]
    action: FAIL
    enabled: true
```

### **2. Generate Baseline Report**

```bash
# Capture current environment state
pyready check . --output baseline.json
```

### **3. Make Changes**

```bash
# Modify your environment (example: change Python version)
# Update pyproject.toml, add dependencies, etc.
```

### **4. Evaluate Policy**

```bash
# Generate new report
pyready check . --output current.json

# Check against policy
pyready diff baseline.json current.json --policy .pyready-policy.yml

# See detailed explanation
pyready diff baseline.json current.json \
  --policy .pyready-policy.yml \
  --explain-policy
```

---

## 📄 Policy File Format

### **YAML Format (Recommended)**

```yaml
version: 1  # Required: Policy schema version

rules:
  - id: unique-rule-id              # Required: Unique identifier
    description: "Human explanation" # Required: What this rule does
    when:                            # Required: Matching conditions
      section: capabilities          # Optional: Which section to match
      key: has_*                     # Optional: Field name (supports wildcards)
      field: status                  # Optional: Sub-field (for checks)
      change_type: changed           # Optional: added, removed, changed
      from: ["true"]                 # Optional: Before values
      to: ["false"]                  # Optional: After values
    action: FAIL                     # Required: FAIL or WARN
    enabled: true                    # Required: true or false
```

### **JSON Format (Alternative)**

```json
{
  "version": 1,
  "rules": [
    {
      "id": "unique-rule-id",
      "description": "Human explanation",
      "when": {
        "section": "capabilities",
        "key": "has_*",
        "change_type": "changed",
        "from": ["true"],
        "to": ["false"]
      },
      "action": "FAIL",
      "enabled": true
    }
  ]
}
```

---

## 🔍 Rule Anatomy

### **Required Fields**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `id` | string | Unique rule identifier (kebab-case) | `no-python-downgrade` |
| `description` | string | Human-readable explanation | `"Prevent Python downgrades"` |
| `when` | object | Conditions to match (see below) | `{section: "checks", ...}` |
| `action` | string | Action when matched: `FAIL` or `WARN` | `FAIL` |
| `enabled` | boolean | Whether rule is active | `true` |

### **Condition Fields (all optional, ANDed together)**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `section` | string | Section to match: `capabilities`, `checks`, `intent`, `run_command`, `recommendations` | `capabilities` |
| `key` | string | Specific key (supports wildcards `*`) | `has_*`, `Python_Version` |
| `field` | string | Sub-field within key (mainly for `checks`) | `status`, `message` |
| `change_type` | string | Type of change: `added`, `removed`, `changed` | `changed` |
| `from` | list[string] | Before values (match any in list) | `["PASS", "WARN"]` |
| `to` | list[string] | After values (match any in list) | `["FAIL"]` |

---

## ⚙️ Matching Logic

### **How Rules Match**

1. **All conditions are ANDed together**
   ```yaml
   when:
     section: checks        # AND
     key: Python_Version    # AND
     field: status          # AND
     to: ["FAIL"]           # All must match
   ```

2. **Wildcard matching (fnmatch)**
   ```yaml
   key: has_*              # Matches: has_python_files, has_venv, etc.
   key: *_status           # Matches: check_status, test_status, etc.
   key: checks.*           # Matches: checks.Python_Version, etc.
   ```

3. **Value extraction**
   - Handles `"Status: PASS"` → extracts `"PASS"`
   - Handles `"PASS"` → uses as-is
   - Case-sensitive matching

4. **List matching (OR within list)**
   ```yaml
   to: ["FAIL", "ERROR"]   # Matches if value is "FAIL" OR "ERROR"
   ```

5. **Missing conditions = always match**
   ```yaml
   when:
     section: checks
     # No 'key' specified = matches ALL keys in 'checks'
   ```

### **Evaluation Order**

1. Load all enabled rules
2. For each diff item, check all rules
3. Collect matching rules
4. Aggregate actions: `FAIL` > `WARN` > `PASS`
5. Return highest severity

---

## 📚 Examples

### **Example 1: Prevent Python Downgrades**

**Goal:** Block merges that downgrade Python version

```yaml
version: 1
rules:
  - id: no-python-downgrade
    description: "Python version must not decrease"
    when:
      section: checks
      key: Python_Version
      field: status
      change_type: changed
      to: ["FAIL"]
    action: FAIL
    enabled: true
```

**How it works:**
- Matches when `checks.Python_Version.status` changes to `FAIL`
- This happens when detected Python version is lower than required
- Exit code 2 blocks merge

---

### **Example 2: Require Virtual Environment**

**Goal:** Warn if virtual environment is removed

```yaml
version: 1
rules:
  - id: require-venv
    description: "Virtual environment must exist"
    when:
      section: capabilities
      key: has_isolated_environment
      change_type: changed
      from: ["true"]
      to: ["false"]
    action: WARN
    enabled: true
```

**How it works:**
- Matches when `has_isolated_environment` changes from `true` to `false`
- Exit code 1 warns but doesn't block merge

---

### **Example 3: Block Dependency Removal**

**Goal:** Prevent accidental dependency removal

```yaml
version: 1
rules:
  - id: no-dependency-removal
    description: "Dependencies cannot be removed"
    when:
      section: capabilities
      key: has_dependency_declaration
      change_type: changed
      from: ["true"]
      to: ["false"]
    action: FAIL
    enabled: true
```

---

### **Example 4: Enforce Lock File**

**Goal:** Require reproducible environments

```yaml
version: 1
rules:
  - id: require-lock-file
    description: "Lock file must be present"
    when:
      section: capabilities
      key: has_reproducible_environment
      change_type: removed
    action: FAIL
    enabled: true
```

---

### **Example 5: Warn on New Check Failures**

**Goal:** Flag any new environment issues

```yaml
version: 1
rules:
  - id: warn-new-failures
    description: "Warn if any check starts failing"
    when:
      section: checks
      field: status
      change_type: changed
      to: ["FAIL"]
    action: WARN
    enabled: true
```

**How it works:**
- No `key` specified → matches ANY check
- Matches when any check status changes to `FAIL`

---

### **Example 6: Prevent Intent Downgrade**

**Goal:** Projects shouldn't regress (app → script)

```yaml
version: 1
rules:
  - id: no-intent-downgrade
    description: "Project intent cannot regress"
    when:
      section: intent
      change_type: changed
      from: ["application", "service"]
      to: ["script", "library"]
    action: FAIL
    enabled: true
```

---

## 🎓 Advanced Patterns

### **Pattern 1: Wildcard Matching**

Match all capability changes:
```yaml
rules:
  - id: track-all-capabilities
    description: "Log all capability changes"
    when:
      section: capabilities
      key: has_*
      change_type: changed
    action: WARN
    enabled: true
```

### **Pattern 2: Multiple Value Matching**

Match multiple status values:
```yaml
rules:
  - id: no-failures-or-errors
    description: "No checks can fail or error"
    when:
      section: checks
      field: status
      to: ["FAIL", "ERROR", "CRITICAL"]
    action: FAIL
    enabled: true
```

### **Pattern 3: Section-Wide Rules**

Match all changes in a section:
```yaml
rules:
  - id: audit-all-check-changes
    description: "Log all check changes"
    when:
      section: checks
      change_type: changed
    action: WARN
    enabled: true
```

### **Pattern 4: Conditional Disabling**

Disable rules based on environment:
```yaml
rules:
  - id: strict-python-version
    description: "Enforce Python version in production"
    when:
      section: checks
      key: Python_Version
      field: status
      to: ["FAIL"]
    action: FAIL
    enabled: false  # Disable in development, enable in CI
```

---

## 📖 Policy Explanations

### **Deterministic Explanations**

PyReady generates **100% deterministic explanations** - no AI involved.

**Example Output:**

```bash
pyready diff baseline.json current.json \
  --policy .pyready-policy.yml \
  --explain-policy
```

```
📖 Policy Explanation
  2 of 3 rules matched

──────────────────────────────────────────────────────────────

Rule: no-python-downgrade
Status: ❌ MATCHED (FAIL)
Reason:
  This rule matched because changes were detected in the 'checks'
  section where the 'Python_Version' field's 'status' changed
  from [PASS] to [FAIL].
  
  Triggered by: checks.Python_Version.status

──────────────────────────────────────────────────────────────

Rule: require-venv
Status: ✓ NOT MATCHED
Reason:
  This rule was evaluated but did not match because no changes
  were detected in the 'capabilities' section where the
  'has_isolated_environment' field changed from [true] to [false].

──────────────────────────────────────────────────────────────

Final Status: FAIL (exit code 2)
```

### **Explanation Export**

```bash
# Export to JSON
pyready diff baseline.json current.json \
  --policy .pyready-policy.yml \
  --explain-policy \
  --output policy-audit.json

# Export to Markdown
pyready diff baseline.json current.json \
  --policy .pyready-policy.yml \
  --explain-policy \
  --output policy-audit.md
```

---

## ✅ Best Practices

### **1. Start Small**

Begin with a few critical rules:
```yaml
version: 1
rules:
  # Start with these 3 rules
  - id: no-python-downgrade
    # ...
  - id: require-venv
    # ...
  - id: require-lock-file
    # ...
```

### **2. Use WARN Before FAIL**

Test rules with `WARN` first:
```yaml
rules:
  - id: experimental-rule
    action: WARN  # Test first
    # Later change to: FAIL
```

### **3. Meaningful IDs and Descriptions**

```yaml
# ❌ BAD
- id: rule1
  description: "Check thing"

# ✅ GOOD
- id: no-python-downgrade
  description: "Prevent Python version downgrades to maintain compatibility"
```

### **4. Document Complex Rules**

```yaml
rules:
  - id: enforce-production-standards
    description: |
      Production environments must have:
      - Virtual environment
      - Lock file (reproducible deps)
      - All checks passing
      This rule prevents deployments with environment issues.
    when:
      section: checks
      field: status
      to: ["FAIL"]
    action: FAIL
    enabled: true
```

### **5. Version Control Policies**

```bash
# Commit policy with code
git add .pyready-policy.yml
git commit -m "feat: Add environment governance policy"
```

### **6. Separate Policies by Environment**

```bash
# Development (lenient)
.pyready-policy-dev.yml

# Staging (moderate)
.pyready-policy-staging.yml

# Production (strict)
.pyready-policy-prod.yml
```

Usage:
```bash
# Development
pyready diff old.json new.json --policy .pyready-policy-dev.yml

# Production
pyready diff old.json new.json --policy .pyready-policy-prod.yml
```

### **7. Test Policies Locally**

```bash
# Before pushing, test policy
pyready check . --output test-report.json
pyready diff baseline.json test-report.json --policy .pyready-policy.yml

# Ensure exit code matches expectations
echo $?  # 0 = PASS, 1 = WARN, 2 = FAIL
```

---

## 🐛 Troubleshooting

### **Issue 1: Policy Always Returns PASS**

**Symptoms:**
- No violations detected
- Exit code always 0

**Causes:**
1. Rule conditions don't match diff items
2. Incorrect section/key names
3. Typos in field names

**Solution:**
```bash
# Debug with --explain-policy
pyready diff old.json new.json \
  --policy .pyready-policy.yml \
  --explain-policy

# Check "Reason" field for each rule
# It shows exactly why rules didn't match
```

### **Issue 2: Rule Matches Unexpectedly**

**Symptoms:**
- Rules trigger when they shouldn't
- Too many false positives

**Causes:**
1. Wildcard matching too broad
2. Missing conditions (match everything)
3. Value extraction issues

**Solution:**
```bash
# Be more specific
# ❌ Too broad
when:
  section: checks

# ✅ More specific
when:
  section: checks
  key: Python_Version
  field: status
```

### **Issue 3: YAML Syntax Errors**

**Symptoms:**
- "Invalid policy file format"
- Parse errors

**Solution:**
```bash
# Validate YAML
python -c "import yaml; yaml.safe_load(open('.pyready-policy.yml'))"

# Common issues:
# - Missing quotes around values with colons
# - Incorrect indentation (use 2 spaces)
# - Missing 'version: 1' at top
```

### **Issue 4: Policy Not Loading**

**Symptoms:**
- Policy file not found
- No policy evaluation

**Solution:**
```bash
# Use absolute path
pyready diff old.json new.json --policy /full/path/.pyready-policy.yml

# Or relative path
pyready diff old.json new.json --policy ./policies/.pyready-policy.yml
```

### **Issue 5: Explanation Not Showing**

**Symptoms:**
- `--explain-policy` flag has no effect

**Causes:**
- Flag requires `--policy` to be specified

**Solution:**
```bash
# ✅ CORRECT
pyready diff old.json new.json \
  --policy .pyready-policy.yml \
  --explain-policy

# ❌ WRONG (missing --policy)
pyready diff old.json new.json --explain-policy
```

---

## 🔄 CI/CD Integration

### **GitHub Actions Example**

```yaml
# .github/workflows/environment-policy.yml
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
          fetch-depth: 0

      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install PyReady
        run: pip install git+https://github.com/AdityaMallela041/PyReady.git

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
            --explain-policy \
            --output /tmp/policy-result.md

      - name: Comment on PR
        if: failure()
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const result = fs.readFileSync('/tmp/policy-result.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: '## 🚨 Policy Violation Detected\n\n' + result
            });
```

### **GitLab CI Example**

```yaml
# .gitlab-ci.yml
environment-policy:
  stage: test
  image: python:3.11
  script:
    - pip install git+https://github.com/AdityaMallela041/PyReady.git
    - git checkout $CI_MERGE_REQUEST_TARGET_BRANCH_NAME
    - pyready check . --output baseline.json
    - git checkout $CI_COMMIT_SHA
    - pyready check . --output current.json
    - pyready diff baseline.json current.json 
        --policy .pyready-policy.yml 
        --explain-policy
  rules:
    - if: $CI_PIPELINE_SOURCE == 'merge_request_event'
  allow_failure: false  # Block on FAIL
```

### **Pre-commit Hook**

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Generate current report
pyready check . --output /tmp/current.json

# Compare with baseline
if [ -f .pyready-baseline.json ]; then
  pyready diff .pyready-baseline.json /tmp/current.json \
    --policy .pyready-policy.yml
  
  EXIT_CODE=$?
  
  if [ $EXIT_CODE -eq 2 ]; then
    echo "❌ Policy violation detected! Commit blocked."
    exit 1
  elif [ $EXIT_CODE -eq 1 ]; then
    echo "⚠️  Policy warnings detected. Review recommended."
  fi
fi

exit 0
```

---

## 📚 Example Policy Library

### **Starter Policy (Recommended)**

```yaml
# .pyready-policy.yml
version: 1

rules:
  # Critical: Python version
  - id: no-python-downgrade
    description: "Prevent Python version downgrades"
    when:
      section: checks
      key: Python_Version
      field: status
      to: ["FAIL"]
    action: FAIL
    enabled: true

  # Important: Virtual environment
  - id: require-venv
    description: "Virtual environment recommended"
    when:
      section: capabilities
      key: has_isolated_environment
      change_type: changed
      from: ["true"]
      to: ["false"]
    action: WARN
    enabled: true

  # Important: Lock file
  - id: require-lock-file
    description: "Lock file must exist for reproducibility"
    when:
      section: capabilities
      key: has_reproducible_environment
      change_type: changed
      from: ["true"]
      to: ["false"]
    action: FAIL
    enabled: true
```

### **Strict Production Policy**

```yaml
# .pyready-policy-prod.yml
version: 1

rules:
  # All checks must pass
  - id: all-checks-pass
    description: "All environment checks must pass in production"
    when:
      section: checks
      field: status
      to: ["FAIL", "WARN"]
    action: FAIL
    enabled: true

  # Must have virtual environment
  - id: require-venv-prod
    description: "Production requires isolated environment"
    when:
      section: capabilities
      key: has_isolated_environment
      to: ["false"]
    action: FAIL
    enabled: true

  # Must have lock file
  - id: require-lock-prod
    description: "Production requires reproducible dependencies"
    when:
      section: capabilities
      key: has_reproducible_environment
      to: ["false"]
    action: FAIL
    enabled: true

  # No intent downgrade
  - id: no-intent-downgrade-prod
    description: "Production cannot regress project complexity"
    when:
      section: intent
      change_type: changed
      from: ["application", "service"]
      to: ["script", "library"]
    action: FAIL
    enabled: true
```

---

## 🎓 Advanced Topics

### **Composite Policies**

Combine multiple policy files:
```bash
# Development + security policies
pyready diff old.json new.json \
  --policy .pyready-policy-dev.yml \
  --policy .pyready-policy-security.yml
```

### **Dynamic Policy Selection**

```bash
# Select policy based on branch
BRANCH=$(git branch --show-current)

if [ "$BRANCH" = "main" ]; then
  POLICY=".pyready-policy-prod.yml"
elif [ "$BRANCH" = "staging" ]; then
  POLICY=".pyready-policy-staging.yml"
else
  POLICY=".pyready-policy-dev.yml"
fi

pyready diff baseline.json current.json --policy $POLICY
```

### **Policy Testing**

Create test cases for your policies:
```bash
# test-policies.sh
#!/bin/bash

# Test 1: Python downgrade should FAIL
echo "Test 1: Python downgrade"
pyready diff test/baseline-py311.json test/pr-py39.json \
  --policy .pyready-policy.yml
if [ $? -eq 2 ]; then
  echo "✅ PASS: Python downgrade correctly blocked"
else
  echo "❌ FAIL: Python downgrade not blocked"
  exit 1
fi

# Test 2: Lock file removal should FAIL
echo "Test 2: Lock file removal"
pyready diff test/baseline-lock.json test/pr-no-lock.json \
  --policy .pyready-policy.yml
if [ $? -eq 2 ]; then
  echo "✅ PASS: Lock file removal correctly blocked"
else
  echo "❌ FAIL: Lock file removal not blocked"
  exit 1
fi
```

---

## 📞 Support

For policy-related questions:

- 🐛 **GitHub Issues:** [Create Issue](https://github.com/AdityaMallela041/PyReady/issues)
- 📖 **Architecture:** See [ARCHITECTURE.md](ARCHITECTURE.md)
- 💬 **Discussions:** [GitHub Discussions](https://github.com/AdityaMallela041/PyReady/discussions)

---

## 📝 Changelog

### **v0.2.0 - Current**
- ✨ Deterministic policy explanation system
- ✨ Wildcard support in `key` matching
- ✨ Template-based explanations (no AI)
- ✨ Export explanations to JSON/Markdown
- 🔒 100% audit compliance

---

**Last Updated:** January 6, 2026  
**Version:** 0.2.0  
**Author:** Aditya Mallela
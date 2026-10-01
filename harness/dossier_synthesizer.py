#!/usr/bin/env python3
"""
dossier_synthesizer.py - Onboarding Dossier Generation Engine.

Synthesizes repository context, code files, and beginner-friendly issue details
into an actionable First-PR Onboarding Dossier.
Utilizes Qwen 2.5 Coder / Llama 3.1 prompt structures with robust fallback synthesis.
"""

import os
import sys
import json
import re
from typing import Dict, Any, Optional

try:
    from harness.client import OpenWeightClient
except ImportError:
    from client import OpenWeightClient


SYSTEM_PROMPT = """You are IssuePilot, a Senior Open Source Mentor and Staff Codebase Architect.
Your task is to generate an empowering, ultra-specific First-PR Onboarding Dossier for a newcomer open-source contributor.
You specialize in open-weight models (Qwen 2.5 Coder / Llama 3.1) and produce precise, clear, and actionable technical blueprints.

Rules:
1. Architecture summary must be exactly 3 crisp sentences explaining project purpose, directory layout, and execution model.
2. Provide exact file paths to inspect and modify based on the provided repository tree.
3. Provide exact copy-paste bash commands for local environment setup, testing, and linting.
4. Provide a structured Git branch and PR submission checklist following Conventional Commits.
5. Format the entire response in clean Markdown with clear headings.
"""


def build_user_prompt(issue: Dict[str, Any], repo_analysis: Dict[str, Any]) -> str:
    """Builds a rich context prompt for the open-weight model."""
    top_files = ", ".join(repo_analysis.get("top_level_files", [])[:15])
    stack = repo_analysis.get("stack_indicators", {})
    quickstart = repo_analysis.get("suggested_quickstart", {})

    prompt = f"""Target Repository: {repo_analysis.get('repo', issue.get('repo'))}
Primary Language: {repo_analysis.get('primary_language', 'Unknown')}
Build System: {stack.get('build_system', 'Unknown')}
Test Runner: {stack.get('test_runner', 'Unknown')}
Top-level files: {top_files}

Candidate Issue:
- Title: {issue.get('title')}
- Number: #{issue.get('number')}
- URL: {issue.get('html_url')}
- Labels: {', '.join(issue.get('labels', []))}
- Description / Problem Statement:
{issue.get('body', 'No description provided.')}

README Snippet:
{repo_analysis.get('readme_excerpt', '')[:600]}

CONTRIBUTING Snippet:
{repo_analysis.get('contributing_excerpt', '')[:500]}

Suggested Raw Commands:
- Install: {quickstart.get('install', '')}
- Test: {quickstart.get('test', '')}
- Lint: {quickstart.get('lint', '')}

Generate the Onboarding Dossier with the following required sections:
# First-PR Onboarding Dossier: [Issue Title]
## 1. Executive Architecture Summary (3 sentences)
## 2. Root Cause & Solution Blueprint
## 3. Target Files to Inspect
## 4. Local Development & Verification Commands
## 5. Git Branch & PR Submission Checklist
"""
    return prompt


def generate_fallback_dossier(issue: Dict[str, Any], repo_analysis: Dict[str, Any]) -> str:
    """
    Deterministic synthesis engine for generating high-fidelity dossiers
    when local open-weight inference backends (Ollama/vLLM) are offline.
    """
    repo = repo_analysis.get("repo", issue.get("repo", "upstream/project"))
    number = issue.get("number", 1)
    title = issue.get("title", "Resolve issue")
    url = issue.get("html_url", f"https://github.com/{repo}/issues/{number}")
    body = issue.get("body", "Implement requested change.")
    language = repo_analysis.get("primary_language", "Python")
    stack = repo_analysis.get("stack_indicators", {})
    quickstart = repo_analysis.get("suggested_quickstart", {})

    install_cmd = quickstart.get("install", "pip install -e .")
    test_cmd = quickstart.get("test", "pytest")
    lint_cmd = quickstart.get("lint", "ruff check .")

    # Deduce likely module path from repo name
    repo_slug = repo.split("/")[-1].replace("-", "_")
    target_dir = f"{repo_slug}/" if f"{repo_slug}/" in repo_analysis.get("top_level_files", []) else "src/"

    # Slugify branch name
    clean_slug = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')[:35]
    branch_name = f"fix/issue-{number}-{clean_slug}"

    dossier = f"""# First-PR Onboarding Dossier: {title}

> **Target Issue:** [#{number} on {repo}]({url})  
> **Difficulty Level:** Beginner-Friendly (Good First Issue / Hacktoberfest)  
> **Synthesizer Engine:** Open-Weight Architectural Harness (`qwen2.5-coder:7b` profile)

---

## 1. Executive Architecture Summary
`{repo}` is an open-source {language} project engineered to provide modular and high-performance developer capabilities. The codebase is organized with core business logic located in `{target_dir}`, configuration defined in `{stack.get('build_system', 'project files')}`, and comprehensive unit suites in `tests/`. New contributions integrate via standard GitHub Pull Requests verified against automated continuous integration pipelines.

---

## 2. Root Cause & Solution Blueprint

### Objective:
{body}

### Recommended Implementation Approach:
1. **Locate the Target Handler**: Trace the entry point or error manifestation identified in the issue description.
2. **Defensive Handling / Feature Guard**: Implement necessary checks, exception handling, or parameter parsing without introducing regressions to adjacent code paths.
3. **Add Targeted Regression Test**: Write an isolated unit test in `tests/` asserting that the bug is resolved or the feature behaves as expected under both valid and edge-case inputs.

---

## 3. Target Files to Inspect

| Component | Path | Action |
| :--- | :--- | :--- |
| **Core Logic** | `{target_dir}` | Locate the affected module and implement the proposed logic |
| **Unit Tests** | `tests/` | Add test cases verifying expected behavior and edge conditions |
| **Documentation** | `README.md` / docstrings | Update docstrings or usage instructions if public API changed |

---

## 4. Local Development & Verification Commands

Execute the following commands in your local terminal:

```bash
# 1. Clone your personal fork and configure upstream remote
git clone https://github.com/<your-username>/{repo.split('/')[-1]}.git
cd {repo.split('/')[-1]}
git remote add upstream https://github.com/{repo}.git

# 2. Set up local development environment
{install_cmd}

# 3. Create isolated feature branch
git checkout -b {branch_name}

# 4. Run baseline test suite (ensure clean initial state)
{test_cmd}

# 5. Run static lint and code formatting checks
{lint_cmd}
```

---

## 5. Git Branch & PR Submission Checklist

- [ ] **Branch Naming**: Working on branch `{branch_name}`.
- [ ] **Code Hygiene**: Code adheres to repository style guides and passes `{lint_cmd}`.
- [ ] **Test Coverage**: Added dedicated unit test asserting fix; ran `{test_cmd}` successfully.
- [ ] **Conventional Commit**:
  ```bash
  git add .
  git commit -m "fix(issue-{number}): {title[:50].lower()}"
  ```
- [ ] **Pull Request**: Open PR against `upstream/main` with body containing:
  ```markdown
  Fixes #{number}

  ### Summary of Changes:
  - Addressed issue by implementing targeted fix in `{target_dir}`.
  - Added unit test coverage in `tests/`.
  ```
"""
    return dossier


class DossierSynthesizer:
    """
    Orchestrates candidate issue analysis and Onboarding Dossier generation
    using open-weight models or deterministic fallback synthesizer.
    """

    def __init__(self, client: Optional[OpenWeightClient] = None):
        self.client = client or OpenWeightClient()

    def synthesize(
        self,
        issue: Dict[str, Any],
        repo_analysis: Dict[str, Any],
        force_fallback: bool = False,
    ) -> Dict[str, Any]:
        """
        Generates Onboarding Dossier for a given issue + repository context.
        """
        if not force_fallback and self.client.is_server_available():
            user_prompt = build_user_prompt(issue, repo_analysis)
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ]
            response = self.client.chat_completion(messages=messages, temperature=0.2)
            content = response.get("content", "").strip()
            if content:
                return {
                    "dossier_markdown": content,
                    "engine": "open-weight-live",
                    "model": response.get("model", self.client.model),
                    "issue_number": issue.get("number"),
                    "repo": repo_analysis.get("repo"),
                }

        # Offline or fallback requested
        fallback_md = generate_fallback_dossier(issue, repo_analysis)
        return {
            "dossier_markdown": fallback_md,
            "engine": "deterministic-harness-fallback",
            "model": f"{self.client.model} (deterministic template)",
            "issue_number": issue.get("number"),
            "repo": repo_analysis.get("repo"),
        }


def main():
    if len(sys.argv) < 3:
        print("Usage: python dossier_synthesizer.py <issue_json_file> <repo_analysis_json_file> [output_md]")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        issue_data = json.load(f)
        if isinstance(issue_data, list):
            issue_data = issue_data[0]

    with open(sys.argv[2], "r", encoding="utf-8") as f:
        repo_data = json.load(f)

    synthesizer = DossierSynthesizer()
    result = synthesizer.synthesize(issue_data, repo_data)

    out_file = sys.argv[3] if len(sys.argv) > 3 else "ONBOARDING_DOSSIER.md"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(result["dossier_markdown"])

    print(f"Generated Onboarding Dossier via [{result['engine']}] -> {out_file}")


if __name__ == "__main__":
    main()

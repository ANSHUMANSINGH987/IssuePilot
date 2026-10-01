#!/usr/bin/env python3
"""
analyze_repo.py - Repository Architecture & Contribution Contextualizer.

Inspects target GitHub repository topology:
- Fetches top-level directory structure
- Detects package management, language, and testing frameworks
- Extracts README setup instructions and CONTRIBUTING.md guidelines
- Formats a compact context payload for open-weight model synthesis
"""

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, List, Optional

# Load local .env
def load_dotenv(filepath: str = ".env") -> None:
    if not os.path.exists(filepath):
        parent_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".env")
        if os.path.exists(parent_env):
            filepath = parent_env
        else:
            return

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, val = line.split("=", 1)
                key, val = key.strip(), val.strip()
                if key and key not in os.environ:
                    os.environ[key] = val.strip("\"'")
    except Exception:
        pass

load_dotenv()


MOCK_REPO_ANALYSES = {
    "psf/requests-toolbelt": {
        "repo": "psf/requests-toolbelt",
        "description": "A utility belt for advanced users of python-requests",
        "primary_language": "Python",
        "default_branch": "master",
        "stars": 1250,
        "stack_indicators": {
            "build_system": "setuptools / pyproject.toml",
            "test_runner": "pytest / tox",
            "linter": "flake8 / black",
            "package_manager": "pip",
        },
        "top_level_files": [
            ".github/", "docs/", "requests_toolbelt/", "tests/",
            ".gitignore", ".travis.yml", "AUTHORS.rst", "CONTRIBUTING.rst",
            "HISTORY.rst", "LICENSE", "Makefile", "README.rst",
            "pyproject.toml", "setup.cfg", "setup.py", "tox.ini"
        ],
        "readme_excerpt": (
            "Requests-Toolbelt is an open-source library extending Requests with "
            "streaming multipart uploads, SSL adapters, and authentication helpers.\n\n"
            "Development Setup:\n"
            "  pip install -e .[dev]\n"
            "  pytest tests/"
        ),
        "contributing_excerpt": (
            "Pull Requests are welcome! Please ensure:\n"
            "1. All new code includes unit tests in tests/\n"
            "2. Run 'tox' or 'pytest' locally to verify pass\n"
            "3. Follow PEP8 style guidelines\n"
            "4. Add yourself to AUTHORS.rst"
        ),
        "suggested_quickstart": {
            "install": "pip install -e .[dev]",
            "test": "pytest tests/ -v",
            "lint": "flake8 requests_toolbelt/ tests/",
        }
    },
    "fastapi/fastapi-cli": {
        "repo": "fastapi/fastapi-cli",
        "description": "Run and manage FastAPI applications from the terminal",
        "primary_language": "Python",
        "default_branch": "main",
        "stars": 2400,
        "stack_indicators": {
            "build_system": "pdm / pyproject.toml",
            "test_runner": "pytest",
            "linter": "ruff",
            "package_manager": "pdm / pip",
        },
        "top_level_files": [
            ".github/", "fastapi_cli/", "tests/", ".gitignore",
            "LICENSE", "README.md", "pyproject.toml"
        ],
        "readme_excerpt": (
            "FastAPI CLI - Command line interface for FastAPI projects.\n"
            "Quickstart:\n"
            "  pip install -e .\n"
            "  pytest"
        ),
        "contributing_excerpt": (
            "Contributing to FastAPI CLI:\n"
            "- Use ruff for linting and formatting.\n"
            "- Ensure 100% test coverage for new CLI arguments."
        ),
        "suggested_quickstart": {
            "install": "pip install -e .",
            "test": "pytest",
            "lint": "ruff check .",
        }
    }
}


def make_github_request(url: str, token: Optional[str] = None) -> Any:
    """Executes authenticated or unauthenticated GitHub API request."""
    token = token or os.environ.get("GITHUB_TOKEN")
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "IssuePilot-FirstPRNavigator/0.1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def decode_file_content(item_data: Dict[str, Any]) -> str:
    """Decodes base64 content returned by GitHub API contents endpoint."""
    content = item_data.get("content", "")
    encoding = item_data.get("encoding", "")
    if encoding == "base64" and content:
        try:
            return base64.b64decode(content).decode("utf-8", errors="replace")
        except Exception:
            return ""
    return content


def infer_stack(file_names: List[str]) -> Dict[str, str]:
    """Infers build system, package manager, and test commands from files."""
    files_set = set(file_names)
    stack = {
        "build_system": "Unknown",
        "test_runner": "Not detected",
        "linter": "Not detected",
        "package_manager": "Not detected",
    }

    # Python
    if any(f in files_set for f in ["pyproject.toml", "setup.py", "requirements.txt", "Pipfile", "tox.ini"]):
        stack["build_system"] = "Python (PEP 517 / setup.py)"
        stack["package_manager"] = "pip / poetry / pdm"
        stack["test_runner"] = "pytest"
        stack["linter"] = "ruff / flake8 / black"
    # Node / TypeScript
    elif "package.json" in files_set:
        stack["build_system"] = "Node.js (npm / yarn / pnpm / bun)"
        stack["package_manager"] = "npm"
        stack["test_runner"] = "npm test (jest / vitest)"
        stack["linter"] = "eslint / prettier"
    # Rust
    elif "Cargo.toml" in files_set:
        stack["build_system"] = "Cargo"
        stack["package_manager"] = "cargo"
        stack["test_runner"] = "cargo test"
        stack["linter"] = "cargo clippy / cargo fmt"
    # Go
    elif "go.mod" in files_set:
        stack["build_system"] = "Go Modules"
        stack["package_manager"] = "go"
        stack["test_runner"] = "go test ./..."
        stack["linter"] = "golangci-lint"

    return stack


def infer_quickstart(stack: Dict[str, str]) -> Dict[str, str]:
    """Provides copy-paste commands based on detected stack."""
    build = stack.get("build_system", "").lower()
    if "python" in build:
        return {
            "install": "pip install -e .",
            "test": "pytest",
            "lint": "ruff check . || flake8 .",
        }
    elif "node" in build:
        return {
            "install": "npm install",
            "test": "npm test",
            "lint": "npm run lint",
        }
    elif "cargo" in build:
        return {
            "install": "cargo build",
            "test": "cargo test",
            "lint": "cargo clippy",
        }
    elif "go" in build:
        return {
            "install": "go build ./...",
            "test": "go test ./...",
            "lint": "golangci-lint run",
        }
    return {
        "install": "See README.md",
        "test": "See CONTRIBUTING.md",
        "lint": "Not configured",
    }


def analyze_github_repo(
    repo: str,
    token: Optional[str] = None,
    use_mock_fallback: bool = True
) -> Dict[str, Any]:
    """
    Analyzes a GitHub repository's structure, README, and contributing guidelines.
    """
    # Clean repo string (handling https://github.com/owner/repo or owner/repo)
    clean_repo = repo.replace("https://github.com/", "").strip("/")
    parts = clean_repo.split("/")
    if len(parts) >= 2:
        owner, repo_name = parts[0], parts[1]
        clean_repo = f"{owner}/{repo_name}"
    else:
        clean_repo = repo

    token = token or os.environ.get("GITHUB_TOKEN")

    try:
        # 1. Fetch Repo Metadata
        repo_data = make_github_request(f"https://api.github.com/repos/{clean_repo}", token=token)
        
        # 2. Fetch Top-Level Contents
        contents_data = make_github_request(f"https://api.github.com/repos/{clean_repo}/contents", token=token)
        top_level_files = []
        if isinstance(contents_data, list):
            for item in contents_data:
                name = item.get("name", "")
                if item.get("type") == "dir":
                    top_level_files.append(name + "/")
                else:
                    top_level_files.append(name)

        # 3. Fetch README snippet
        readme_excerpt = "No README detected."
        try:
            readme_data = make_github_request(f"https://api.github.com/repos/{clean_repo}/readme", token=token)
            raw_readme = decode_file_content(readme_data)
            readme_excerpt = raw_readme[:1500] if raw_readme else readme_excerpt
        except Exception:
            pass

        # 4. Fetch CONTRIBUTING snippet
        contributing_excerpt = "No CONTRIBUTING.md found. Refer to standard Git PR workflow."
        for possible_path in ["CONTRIBUTING.md", ".github/CONTRIBUTING.md", "CONTRIBUTING.rst"]:
            try:
                contrib_data = make_github_request(
                    f"https://api.github.com/repos/{clean_repo}/contents/{urllib.parse.quote(possible_path)}",
                    token=token
                )
                raw_contrib = decode_file_content(contrib_data)
                if raw_contrib:
                    contributing_excerpt = raw_contrib[:1500]
                    break
            except Exception:
                continue

        stack = infer_stack(top_level_files)
        quickstart = infer_quickstart(stack)

        return {
            "repo": clean_repo,
            "description": repo_data.get("description") or "Open source project",
            "primary_language": repo_data.get("language") or "Multi-language",
            "default_branch": repo_data.get("default_branch", "main"),
            "stars": repo_data.get("stargazers_count", 0),
            "stack_indicators": stack,
            "top_level_files": top_level_files,
            "readme_excerpt": readme_excerpt,
            "contributing_excerpt": contributing_excerpt,
            "suggested_quickstart": quickstart,
        }

    except urllib.error.HTTPError as e:
        sys.stderr.write(f"[WARN] GitHub API error analyzing {clean_repo}: {e.code} {e.reason}\n")
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to analyze repository {clean_repo}: {e}\n")

    if use_mock_fallback:
        sys.stderr.write(f"[INFO] Using fixture profile for repository analysis: {clean_repo}\n")
        if clean_repo in MOCK_REPO_ANALYSES:
            return MOCK_REPO_ANALYSES[clean_repo]
        
        # Generic fallback
        return {
            "repo": clean_repo,
            "description": "Open source repository analyzed by IssuePilot",
            "primary_language": "Python",
            "default_branch": "main",
            "stars": 100,
            "stack_indicators": {
                "build_system": "pyproject.toml / setup.py",
                "test_runner": "pytest",
                "linter": "ruff",
                "package_manager": "pip",
            },
            "top_level_files": ["src/", "tests/", "README.md", "pyproject.toml", "LICENSE"],
            "readme_excerpt": "Standard open-source library setup with pytest test suite.",
            "contributing_excerpt": "Open a pull request on a feature branch with clean commit messages and passing tests.",
            "suggested_quickstart": {
                "install": "pip install -e .",
                "test": "pytest",
                "lint": "ruff check .",
            }
        }

    return {}


def main():
    parser = argparse.ArgumentParser(description="Analyze GitHub repository structure and contribution guidelines.")
    parser.add_argument("--repo", "-r", type=str, required=True, help="GitHub repository (owner/repo or full URL)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Optional output JSON file path")
    parser.add_argument("--no-mock", action="store_true", help="Disable mock fallback when API calls fail")

    args = parser.parse_args()

    analysis = analyze_github_repo(args.repo, use_mock_fallback=not args.no_mock)
    json_output = json.dumps(analysis, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"Repository analysis written to {args.output}")
    else:
        print(json_output)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
test_pipeline.py - Automated Test Suite for IssuePilot (First-PR Navigator).

Validates:
1. Candidate issue discovery & fixture fallback behavior
2. Repository contextualization and stack inference
3. Open-weight client resilience and offline fallback handling
4. Onboarding dossier synthesis and markdown section completeness
5. FastAPI web server endpoints (/api/health, /api/scan, /api/dossier, /)
"""

import os
import sys
import urllib.error
from pathlib import Path
import pytest

# Ensure root, scripts, harness, and web directories are in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "first-pr-navigator" / "scripts"
HARNESS_DIR = PROJECT_ROOT / "harness"
WEB_DIR = PROJECT_ROOT / "web"

for p in [str(PROJECT_ROOT), str(SCRIPTS_DIR), str(HARNESS_DIR), str(WEB_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

import scan_issues
from scan_issues import find_candidate_issues, build_search_query
from analyze_repo import analyze_github_repo, infer_stack, infer_quickstart
from harness.client import OpenWeightClient
from harness.dossier_synthesizer import DossierSynthesizer, generate_fallback_dossier
from web.server import app
from fastapi.testclient import TestClient


# ==============================================================================
# Unit & Integration Tests: Issue Discovery
# ==============================================================================
def test_build_search_query():
    """Validates GitHub issue search query construction."""
    query = build_search_query(language="python", topic="cli", max_comments=5)
    assert "is:issue" in query
    assert "is:open" in query
    assert "no:assignee" in query
    assert "comments:<5" in query
    assert "language:python" in query
    assert "cli" in query


def test_issue_scanner_fallback():
    """Validates candidate issue discovery output and structure."""
    issues = find_candidate_issues(language="python", limit=2, use_mock_fallback=True)
    assert len(issues) >= 1
    sample = issues[0]
    required_keys = ["id", "number", "title", "repo", "html_url", "labels", "comments", "body"]
    for k in required_keys:
        assert k in sample, f"Missing key '{k}' in discovered candidate issue"
    assert isinstance(sample["labels"], list)
    assert sample["url"] == sample["html_url"]


def test_expanded_query_aliases():
    """Validates friendly language and domain values become GitHub qualifiers."""
    csharp_query = build_search_query(language="c#", topic="cybersecurity")
    docs_query = build_search_query(language="any", topic="docs")
    ai_query = build_search_query(language="cpp", topic="ai")

    assert 'language:"C#"' in csharp_query
    assert "topic:security" in csharp_query and "topic:infosec" in csharp_query
    assert "language:" not in docs_query
    assert 'label:"documentation"' in docs_query and 'label:"docs"' in docs_query
    assert 'language:"C++"' in ai_query
    assert "topic:machine-learning" in ai_query


def test_expanded_fixture_filters(monkeypatch):
    """Validates offline fixtures cover domain and effort filters."""
    def raise_offline(*args, **kwargs):
        raise urllib.error.URLError("offline")

    monkeypatch.setattr(scan_issues.urllib.request, "urlopen", raise_offline)
    docs = find_candidate_issues(language="any", topic="docs", limit=20)
    mobile = find_candidate_issues(language="kotlin", topic="mobile", effort="quick", limit=20)

    assert docs and all(issue["domain"] == "docs" for issue in docs)
    assert mobile and mobile[0]["language"] == "kotlin"
    assert mobile[0]["effort"] == "quick"


# ==============================================================================
# Unit & Integration Tests: Repository Contextualization
# ==============================================================================
def test_stack_inference():
    """Validates build stack and test runner detection from file manifests."""
    python_stack = infer_stack(["pyproject.toml", "tests/", "README.md"])
    assert "Python" in python_stack["build_system"]
    assert "pytest" in python_stack["test_runner"]

    node_stack = infer_stack(["package.json", "src/"])
    assert "Node.js" in node_stack["build_system"]

    rust_stack = infer_stack(["Cargo.toml", "src/"])
    assert "Cargo" in rust_stack["build_system"]

    go_stack = infer_stack(["go.mod", "main.go"])
    assert "Go" in go_stack["build_system"]


def test_repo_analyzer_structure():
    """Validates repository analysis output and quickstart command inference."""
    analysis = analyze_github_repo("psf/requests-toolbelt", use_mock_fallback=True)
    assert analysis["repo"] == "psf/requests-toolbelt"
    assert "stack_indicators" in analysis
    assert "suggested_quickstart" in analysis
    assert "install" in analysis["suggested_quickstart"]
    assert "test" in analysis["suggested_quickstart"]


# ==============================================================================
# Unit & Integration Tests: Model Harness & Dossier Synthesis
# ==============================================================================
def test_open_weight_client_offline_handling():
    """Validates that OpenWeightClient handles offline endpoints safely."""
    # Point to an arbitrary unreachable port
    client = OpenWeightClient(api_base="http://127.0.0.1:54321/v1", timeout=2)
    assert not client.is_server_available()
    res = client.chat_completion(messages=[{"role": "user", "content": "hi"}])
    assert res["provider"] in ["offline", "error"]


def test_dossier_synthesis_markdown():
    """Validates that the synthesized Onboarding Dossier contains all required sections."""
    issue = {
        "number": 42,
        "title": "Add retry mechanism with exponential backoff",
        "repo": "psf/requests-toolbelt",
        "html_url": "https://github.com/psf/requests-toolbelt/issues/42",
        "body": "Add retry mechanism for HTTP 503 failures.",
        "language": "python",
    }
    repo_analysis = analyze_github_repo("psf/requests-toolbelt", use_mock_fallback=True)

    synthesizer = DossierSynthesizer(client=OpenWeightClient(api_base="http://127.0.0.1:54321/v1", timeout=1))
    result = synthesizer.synthesize(issue, repo_analysis, force_fallback=True)

    assert result["success"] if "success" in result else True
    md = result["dossier_markdown"]

    # Verify standard sections required by specification
    assert "Executive Architecture Summary" in md
    assert "Root Cause & Solution Blueprint" in md
    assert "Target Files to Inspect" in md
    assert "Local Development & Verification Commands" in md
    assert "Git Branch & PR Submission Checklist" in md
    assert "fix(issue-42)" in md
    assert "Fixes #42" in md


# ==============================================================================
# Integration Tests: FastAPI Endpoints
# ==============================================================================
client = TestClient(app)

def test_api_health():
    """Tests GET /api/health endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "open_weight_model" in data
    assert "open_weight_status" in data


def test_api_scan():
    """Tests POST /api/scan endpoint."""
    response = client.post("/api/scan", json={"language": "python", "limit": 2})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["issues"], list)
    assert len(data["issues"]) > 0


def test_api_scan_expanded_filters(monkeypatch):
    """Validates the web API forwards the expanded selector state."""
    captured = {}

    def fake_scan(**kwargs):
        captured.update(kwargs)
        return []

    import web.server as web_server
    monkeypatch.setattr(web_server, "find_candidate_issues", fake_scan)
    response = client.post(
        "/api/scan",
        json={
            "language": "Kotlin",
            "topic": "mobile",
            "experience": "moderate",
            "effort": "quick",
            "limit": 4,
        },
    )

    assert response.status_code == 200
    assert captured == {
        "language": "Kotlin",
        "topic": "mobile",
        "effort": "quick",
        "limit": 4,
        "repo": None,
        "use_mock_fallback": True,
    }
    assert response.json()["filters"]["experience"] == "moderate"


def test_api_dossier():
    """Tests POST /api/dossier endpoint."""
    payload = {
        "repo": "psf/requests-toolbelt",
        "number": 42,
        "title": "Add retry mechanism with exponential backoff",
        "language": "python",
    }
    response = client.post("/api/dossier", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "dossier_markdown" in data
    assert "Executive Architecture Summary" in data["dossier_markdown"]


def test_api_serve_frontend():
    """Tests GET / root endpoint serving index.html."""
    response = client.get("/")
    assert response.status_code == 200
    assert "IssuePilot" in response.text

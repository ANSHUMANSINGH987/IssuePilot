#!/usr/bin/env python3
"""
server.py - FastAPI Bridge for IssuePilot (First-PR Navigator).

Bridges the web dashboard frontend with:
- scan_issues.py (Candidate Issue Discovery)
- analyze_repo.py (Repository Contextualization)
- harness/dossier_synthesizer.py (Open-Weight Model Dossier Synthesis)
"""

import os
import sys
from typing import Optional, List, Dict, Any
from pathlib import Path

# Setup paths to import from first-pr-navigator and harness
BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "first-pr-navigator" / "scripts"
HARNESS_DIR = BASE_DIR / "harness"

for p in [str(BASE_DIR), str(SCRIPTS_DIR), str(HARNESS_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from scan_issues import find_candidate_issues
from analyze_repo import analyze_github_repo
from harness.client import OpenWeightClient
from harness.dossier_synthesizer import DossierSynthesizer

app = FastAPI(
    title="IssuePilot (First-PR Navigator) API",
    description="Bridge API for open-weight AI agent onboarding contributors for Hacktoberfest",
    version="0.1.0"
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Open-Weight Client and Synthesizer
client = OpenWeightClient()
synthesizer = DossierSynthesizer(client=client)


class ScanRequest(BaseModel):
    language: Optional[str] = ""
    topic: Optional[str] = None
    experience: Optional[str] = None
    effort: Optional[str] = None
    limit: Optional[int] = 6
    repo: Optional[str] = None


class DossierRequest(BaseModel):
    repo: str
    number: Optional[int] = 1
    issue_number: Optional[int] = None
    title: Optional[str] = "Good First Issue"
    issue_title: Optional[str] = None
    html_url: Optional[str] = ""
    issue_url: Optional[str] = None
    body: Optional[str] = ""
    issue_body: Optional[str] = None
    language: Optional[str] = "Python"


@app.get("/api/health")
def get_health() -> Dict[str, Any]:
    """Checks GitHub token and Open-Weight backend availability."""
    github_token_present = bool(os.environ.get("GITHUB_TOKEN"))
    server_online = client.is_server_available()

    return {
        "status": "healthy",
        "github_token_configured": github_token_present,
        "open_weight_endpoint": client.api_base,
        "open_weight_model": client.model,
        "open_weight_status": "ONLINE (Live Inference)" if server_online else "OFFLINE (Intelligent Fallback Active)",
        "mode": "live" if server_online else "fallback",
    }


@app.post("/api/scan")
def scan_issues_endpoint(req: ScanRequest) -> Dict[str, Any]:
    """Discovers beginner-friendly candidate issues matching filters."""
    try:
        limit = max(1, min(req.limit if req.limit is not None else 6, 20))
        issues = find_candidate_issues(
            language=req.language,
            topic=req.topic,
            effort=req.effort,
            limit=limit,
            repo=req.repo,
            use_mock_fallback=True
        )
        return {
            "success": True,
            "count": len(issues),
            "filters": {
                "language": req.language,
                "topic": req.topic,
                "experience": req.experience,
                "effort": req.effort,
                "limit": limit,
            },
            "issues": issues,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/dossier")
def generate_dossier_endpoint(req: DossierRequest) -> Dict[str, Any]:
    """Generates an Onboarding Dossier for a selected issue."""
    try:
        # Standardize fields
        num = req.issue_number or req.number or 1
        tit = req.issue_title or req.title or f"Issue #{num}"
        url = req.issue_url or req.html_url or f"https://github.com/{req.repo}/issues/{num}"
        bdy = req.issue_body or req.body or "Resolve open issue."

        issue_payload = {
            "number": num,
            "title": tit,
            "repo": req.repo,
            "html_url": url,
            "body": bdy,
            "language": req.language or "python",
        }

        # 1. Analyze repo
        repo_analysis = analyze_github_repo(req.repo, use_mock_fallback=True)

        # 2. Synthesize dossier
        result = synthesizer.synthesize(issue_payload, repo_analysis)

        return {
            "success": True,
            "repo": req.repo,
            "issue_number": num,
            "issue_title": tit,
            "engine": result["engine"],
            "model": result["model"],
            "repo_analysis": repo_analysis,
            "dossier_markdown": result["dossier_markdown"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount static directory for frontend
STATIC_DIR = BASE_DIR / "web" / "static"
if not STATIC_DIR.exists():
    STATIC_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "IssuePilot API is running. Place index.html into web/static/."}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    print(f"Starting IssuePilot server on http://localhost:{port}")
    if Path.cwd().resolve() == BASE_DIR:
        uvicorn.run("web.server:app", host="0.0.0.0", port=port, reload=True)
    else:
        uvicorn.run(app, host="0.0.0.0", port=port)

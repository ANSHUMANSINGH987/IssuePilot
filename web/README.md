# IssuePilot Web Dashboard

An aesthetic, Linear/Vercel-inspired dark-mode dashboard for beginner open-source contributors participating in Hacktoberfest.

## Architecture

- **Backend**: FastAPI server (`web/server.py`) exposing:
  - `GET /api/health`: Health checks for GitHub token and open-weight model backend.
  - `POST /api/scan`: Candidate starter issue discovery.
  - `POST /api/dossier`: Repository analysis & Onboarding Dossier synthesis.
- **Frontend**: Clean, dependency-free responsive dashboard in `web/static/`:
  - Contributor profiling bar (Languages: Python, TypeScript, Go, Rust, C++; Domains: CLI, Web, AI/ML, Docs; Experience level toggle).
  - "⚡ Load Demo Profile" preset button for immediate hackathon evaluation.
  - Bento Grid of starter issues with Hacktoberfest badges and availability indicators.
  - Slide-out Onboarding Dossier Drawer with 1-click copyable bash setup commands and Conventional Commit checklists.

## Running the Web Dashboard

```bash
# Start the FastAPI server
python web/server.py
```
Open your browser at: **`http://localhost:8000`**

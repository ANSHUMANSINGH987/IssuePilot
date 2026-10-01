# IssuePilot (First-PR Navigator) 🚀

> **An Autonomous Agent Skill & Open-Weight Model Harness for First-Time Open-Source Contributors**  
> *Built for MLH Hacktoberfest 2026 • Published under the MIT License*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Standard: AgentSkills.io](https://img.shields.io/badge/Standard-agentskills.io-blue.svg)](first-pr-navigator/SKILL.md)
[![Model: Open-Weight](https://img.shields.io/badge/Model-Qwen%202.5%20Coder%20%7C%20Llama%203.1-purple.svg)](harness/)
[![Theme: Linear Dark](https://img.shields.io/badge/UI-Linear%2FVercel%20Aesthetic-black.svg)](web/)

---

## 🌟 Overview

**IssuePilot** transforms open-source newcomers into confident code contributors by eliminating the cognitive overload of exploring unfamiliar repositories. It systematically diagnoses contributor capabilities, discovers unassigned "starter" issues (`good first issue`, `hacktoberfest`, `help wanted`), contextualizes repository architecture, and synthesizes an actionable **First-PR Onboarding Dossier**.

---

## 🏗️ Architecture

```
IssuePilot
├── first-pr-navigator/             # Agent Skill (agentskills.io standard)
│   ├── SKILL.md                    # Standard frontmatter & 4-stage workflow
│   ├── scripts/
│   │   ├── scan_issues.py          # GitHub issue candidate discovery
│   │   └── analyze_repo.py         # Repo topology & toolchain extractor
│   └── references/
│       └── git_workflow.md         # Forking, Conventional Commits & squash-merge hygiene
├── harness/                        # Open-Weight Model Runtime
│   ├── client.py                   # Async OpenAI-compatible client (Ollama/vLLM)
│   ├── dossier_synthesizer.py      # Qwen 2.5 Coder & Llama 3.1 prompt synthesis
│   └── test_run.py                 # End-to-end integration test runner
├── web/                            # Contributor Web Dashboard
│   ├── server.py                   # FastAPI REST API bridge
│   └── static/                     # Dark mode Linear/Vercel UI (HTML/CSS/JS)
└── LICENSE                         # MIT License (2026 IssuePilot Contributors)
```

---

## ⚡ Quickstart (For Hackathon Judges)

### 1. Launch the Web Dashboard
```bash
# Start the FastAPI server (runs on port 8000 by default)
python web/server.py
# Or run from the project root with Uvicorn's reload support
uvicorn web.server:app --reload
```
Open **`http://localhost:8000`** in your browser.

- Click **`⚡ Load Demo Profile`** to load a verified first-timer preset.
- Explore candidate starter issues with live Hacktoberfest badges.
- Click **`Generate Dossier`** to launch the slide-out onboarding drawer featuring:
  - 3-sentence executive repository architecture summary
  - Target files to inspect
  - Copy-paste local development script with 1-click clipboard button
  - Conventional Commit & PR checklist

---

### 2. Run the CLI End-to-End Pipeline
```bash
# Execute end-to-end scan -> analyze -> synthesis flow
python harness/test_run.py --language python
```
Sample generated dossier is saved to: `output/dossier_issue_42.md`.

### 3. Run the Test Suite
```bash
pytest tests/
```

---

## 🤖 Open-Weight Model Integration

IssuePilot connects to local or remote open-weight inference backends via standard OpenAI-compatible endpoints:

- **Target Backend**: Ollama, vLLM, SGLang, or LM Studio
- **Default Base**: `http://localhost:11434/v1`
- **Default Model**: `qwen2.5-coder:7b` (or `llama3.1:8b`)
- **Offline Resilience**: When local inference endpoints are offline, IssuePilot automatically activates its deterministic architectural fallback engine to ensure zero crashes and consistent developer guidance.

---

## 📜 Agent Skill Open Standard Conformance

The `first-pr-navigator` skill conforms strictly to the [Agent Skill Open Standard](https://agentskills.io):
- **YAML Frontmatter**: Standard-compliant fields (`name`, `allowed-tools: "bash file_read http_request"`, string-only `metadata` including the skill version).
- **Standard Layout**: Root `SKILL.md`, deterministic tooling in `scripts/`, domain references in `references/`.
- **4-Stage Pipeline**:
  1. *Contributor Profiling*
  2. *Candidate Issue Discovery*
  3. *Repository Contextualization*
  4. *Onboarding Dossier Synthesis*

---

## 📄 License
Published under the [MIT License](LICENSE) — Copyright (c) 2026 IssuePilot Contributors.

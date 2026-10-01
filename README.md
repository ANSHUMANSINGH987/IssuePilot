# IssuePilot (First-PR Navigator)

IssuePilot helps a first-time contributor move from **"I found an issue"** to **"I know how to submit the pull request."** It matches a contributor's background with approachable open-source issues, explains the target repository, and produces a practical First-PR Onboarding Dossier.

Built for the MLH Hacktoberfest 2026 challenge and released under the [MIT License](LICENSE).

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Standard: AgentSkills.io](https://img.shields.io/badge/Standard-agentskills.io-blue.svg)](first-pr-navigator/SKILL.md)
[![Model: Open-Weight](https://img.shields.io/badge/Model-Qwen%202.5%20Coder%20%7C%20Llama%203.1-purple.svg)](harness/)

## What It Does

A beginner usually has three separate questions:

1. **Which issue is realistic for me?**
2. **Where in this unfamiliar repository would I make the change?**
3. **What commands and PR conventions do I need to follow?**

IssuePilot answers those questions as one workflow:

```text
Contributor profile
        |
        v
Issue discovery  --->  Repository analysis  --->  Onboarding Dossier
        |                         |                       |
        v                         v                       v
Language, domain,        Build files, tests,       Target files, setup,
experience, effort       README, contribution     verification, PR checklist
                         guidelines
```

The result is guidance a student can act on, not only an issue list or a model-generated summary.

## How The System Works

### 1. Profile

The dashboard accepts broad technology and contribution preferences:

- Languages from Python, JavaScript, TypeScript, Java, C++, Go, Rust, C#, Kotlin, Swift, Dart, PHP, Ruby, Zig, Elixir, and Solidity, plus any custom GitHub language.
- Domains such as AI/ML and agents, web/API, frontend/UI, cloud/DevOps, cybersecurity, CLI tools, mobile, and technical writing.
- Experience level and expected effort: quick win, standard, or deep dive.

`Any` selections are sent as empty or omitted filters. A custom language takes priority over a standard language chip.

### 2. Discover Issues

`first-pr-navigator/scripts/scan_issues.py` queries the GitHub Search API for open, unassigned issues with low comment counts and beginner-friendly labels. Friendly dashboard values are translated into GitHub search syntax, for example:

- `C++` becomes `language:"C++"`.
- `C#` becomes `language:"C#"`.
- AI/ML becomes `topic:ai`, `topic:machine-learning`, `topic:llm`, or `topic:agents`.
- Cybersecurity becomes `topic:security` or `topic:infosec`.
- Documentation uses `documentation` or `docs` labels instead of a programming-language qualifier.

When GitHub is unavailable or rate-limited, the scanner uses deterministic fixtures covering CLI, systems, AI, web/frontend, cloud/DevOps, mobile, cybersecurity, and documentation paths.

### 3. Analyze The Repository

`first-pr-navigator/scripts/analyze_repo.py` inspects repository metadata, top-level files, build manifests, README content, contribution guidance, and likely test/lint commands. It returns a compact context object for dossier generation.

### 4. Synthesize The Dossier

`harness/dossier_synthesizer.py` combines the issue and repository context into five sections:

1. Executive architecture summary
2. Root cause and solution blueprint
3. Target files to inspect
4. Local development and verification commands
5. Git branch and PR submission checklist

If an OpenAI-compatible model endpoint is available, the harness uses it. Otherwise it produces the same structure through a deterministic fallback, so the dashboard remains usable offline.

## Run It Locally

### Requirements

- Python 3.10 or newer
- `fastapi`, `uvicorn`, and `pytest`
- Optional: a GitHub token for higher API rate limits
- Optional: Ollama, vLLM, SGLang, LM Studio, or Hugging Face Router for live model inference

Install the Python dependencies in your environment, then create local configuration from the template:

```powershell
Copy-Item .env.example .env
```

Keep `.env` local. It is ignored by Git and must never contain credentials committed to the repository.

### Start The Dashboard

From the project root, use either command:

```bash
python web/server.py
```

```bash
uvicorn web.server:app --reload
```

Open <http://localhost:8000>. The **Load Demo Profile** button selects a predictable Python/CLI/first-timer profile and loads the offline-friendly candidate flow.

### Run The CLI Pipeline

```bash
python first-pr-navigator/scripts/scan_issues.py --language python --limit 3
python harness/test_run.py --language python
```

The end-to-end command writes a dossier to `output/dossier_issue_42.md` by default. A custom output filename is also supported:

```bash
python harness/test_run.py --output dossier.md
```

### Run Tests

```bash
pytest -v
```

The suite covers scanner fallback and query aliases, repository inference, offline model behavior, dossier structure, expanded filter forwarding, and the FastAPI endpoints.

## API Surface

The dashboard is a thin client over four routes:

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Reports GitHub configuration and live/fallback model status. |
| `POST /api/scan` | Returns candidate issues for language, domain, experience, effort, and repository filters. |
| `POST /api/dossier` | Analyzes a selected repository and generates its onboarding dossier. |
| `GET /` | Serves the dashboard. |

An example scan request is:

```json
{
  "language": "kotlin",
  "topic": "mobile",
  "experience": "first-timer",
  "effort": "quick",
  "limit": 6
}
```

The API clamps `limit` to 1 through 20. Issue records expose both `html_url` and the compatible `url` alias.

## Configure An Open-Weight Model

The harness uses the OpenAI-compatible `/chat/completions` contract. Configure the endpoint and model in `.env`:

```dotenv
OPEN_WEIGHT_API_BASE=http://localhost:11434/v1
OPEN_WEIGHT_API_KEY=EMPTY
OPEN_WEIGHT_MODEL=qwen2.5-coder:7b
```

Hugging Face Router is also supported:

```dotenv
OPEN_WEIGHT_API_BASE=https://router.huggingface.co/v1
OPEN_WEIGHT_API_KEY=<your-token>
OPEN_WEIGHT_MODEL=deepseek-ai/DeepSeek-R1:fastest
```

The client preserves model identifiers containing colons and sends `Authorization: Bearer <OPEN_WEIGHT_API_KEY>` to `/chat/completions`.

## Agent Skill Standard

The `first-pr-navigator` directory is an Agent Skill following the [Agent Skills Open Standard](https://agentskills.io):

```text
first-pr-navigator/
├── SKILL.md                 # YAML metadata and four-phase instructions
├── scripts/
│   ├── scan_issues.py       # Issue discovery and offline fixtures
│   └── analyze_repo.py      # Repository context extraction
└── references/
    └── git_workflow.md      # Fork, upstream, branch, and PR guidance
```

The skill's four phases are contributor profiling, candidate issue discovery, repository contextualization, and dossier synthesis. Its `allowed-tools` declaration is kept in the standard space-separated format.

## Repository Map

```text
harness/                    Open-weight client and dossier synthesis
web/                        FastAPI server and dashboard assets
tests/                      Unit and endpoint regression tests
output/                     Example generated dossier
LICENSE                     MIT license
```

## License

IssuePilot is published under the [MIT License](LICENSE).

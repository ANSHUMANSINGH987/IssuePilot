---
name: first-pr-navigator
description: "Autonomous onboarding assistant that profiles open-source contributors, discovers beginner-accessible issues, contextualizes repository architecture, and synthesizes step-by-step contribution dossiers for Hacktoberfest."
compatibility: "antigravity >= 1.0.0, python >= 3.10"
license: MIT
allowed-tools: "bash file_read http_request"
metadata:
   version: "0.1.0"
  tags: "hacktoberfest, good-first-issue, onboarding, code-navigation"
  author: "IssuePilot Team"
  repository: "https://github.com/issuepilot/first-pr-navigator"
  category: "developer-tooling"
---

# First-PR Navigator (IssuePilot Skill)

`first-pr-navigator` guides new contributors through their first pull request on open-source repositories. It eliminates the cognitive overload of exploring unfamiliar codebases by systematically diagnosing developer capabilities, identifying vetted "starter" issues, analyzing repository topology, and generating an actionable Onboarding Dossier.

---

## Skill Architecture & Operational Pipeline

```
+--------------------------+
|  1. Contributor Profile  | -> Languages, Frameworks, Experience, Tooling
+--------------------------+
             |
             v
+--------------------------+
|  2. Issue Discovery      | -> 'good first issue', 'hacktoberfest', 'help wanted'
+--------------------------+
             |
             v
+--------------------------+
| 3. Repo Contextualize    | -> Architecture, Test Suites, Contribution Specs
+--------------------------+
             |
             v
+--------------------------+
|  4. Dossier Synthesis    | -> Step-by-Step Blueprint & Verification Checklist
+--------------------------+
```

---

## Phase 1: Contributor Profiling

Before scanning repositories, extract or prompt for contributor preferences:
1. **Core Language Competency**: e.g., TypeScript/JavaScript, Python, Go, Rust, or Java.
2. **Framework Exposure**: e.g., React, FastAPI, Express, Django, Next.js.
3. **Contribution Scope**:
   - `docs`: Documentation, typos, tutorials, API references.
   - `tests`: Test coverage improvements, mocking, unit tests.
   - `bugfix`: Small isolated bug fixes with clear reproduction steps.
   - `feature`: Scoped micro-features or CLI subcommands.
4. **Environment Setup Preference**: Docker vs. local virtual environments / npm.

---

## Phase 2: Candidate Issue Discovery

Locate actionable issues matching the profile while filtering out stalled, disputed, or heavily claimed tickets.

### Discovery Criteria:
- **Labels**: `good first issue`, `hacktoberfest`, `help wanted`, `beginner-friendly`, `easy`.
- **State**: Open, zero active assignees, no linked merged PRs or recent active PR drafts claiming the fix.
- **Clarity Index**:
  - Issue specifies current behavior vs. expected behavior.
  - Contains minimal reproduction steps or points directly to the affected module.
  - Contains positive maintainer responsiveness (no unresolved architectural debates).

### Tool Execution Pattern:
Use `http_request` to query the GitHub REST API or `bash` with `gh` CLI:
```bash
# Query open, unassigned good-first-issues tagged for Hacktoberfest
gh issue list --repo <owner>/<repo> \
  --state open \
  --label "good first issue" \
  --search "no:assignee" \
  --limit 10 \
  --json number,title,labels,comments,url,createdAt
```

---

## Phase 3: Repository Contextualization

Inspect the repository architecture and developer workflows to prevent contributors from getting stuck during local setup or testing.

### Workflow:
1. **Detect Build & Package System**:
   - Node: Inspect `package.json` for test scripts (`test`, `lint`, `build`).
   - Python: Inspect `pyproject.toml`, `setup.cfg`, `requirements.txt`, or `Pipfile`.
   - Go: Inspect `go.mod` and `Makefile`.
   - Rust: Inspect `Cargo.toml`.
2. **Review Contribution Guidelines**:
   - Read `CONTRIBUTING.md`, `README.md`, or `.github/PULL_REQUEST_TEMPLATE.md` using `file_read`.
   - Note required commit message conventions (e.g., Conventional Commits) and branch naming policies.
3. **Map Code Boundaries**:
   - Trace the issue topic to candidate directories (e.g., `src/`, `lib/`, `tests/`).
   - Identify relevant unit/integration tests that exercise the targeted code path.

---

## Phase 4: Onboarding Dossier Synthesis

Synthesize findings into an interactive **Onboarding Dossier** formatted in Markdown.

### Required Dossier Sections:

1. **Issue Briefing**:
   - Issue title, number, link, and concise summary of the objective.
   - Why this issue matches the contributor's skill profile.

2. **Local Environment Quickstart**:
   ```bash
   # 1. Clone fork and set upstream
   git clone https://github.com/<contributor>/<repo>.git
   cd <repo>
   git remote add upstream https://github.com/<upstream-owner>/<repo>.git

   # 2. Install dependencies
   <package_manager_install_command>

   # 3. Create feature branch
   git checkout -b <branch-name>
   ```

3. **Code Navigation & Blueprint**:
   - **Target Files**: Explicit file paths requiring edits.
   - **Context & Pointers**: Key functions, classes, or configuration lines.
   - **Recommended Approach**: Concrete suggestions on how to implement the fix safely.

4. **Testing & Quality Assurance**:
   - Command to run targeted tests before making changes (asserting baseline).
   - Command to execute relevant unit tests during development.
   - Linting and format checking commands (`npm run lint`, `ruff check`, etc.).

5. **PR Submission Checklist**:
   - [ ] Branch up to date with `upstream/main`.
   - [ ] Conventional Commit message formatted properly (`feat: ...` / `fix: ...`).
   - [ ] Tests passing locally.
   - [ ] PR description links issue with `Fixes #<issue-id>`.

---

## References

- [Git & GitHub Collaboration Workflow](references/git_workflow.md)

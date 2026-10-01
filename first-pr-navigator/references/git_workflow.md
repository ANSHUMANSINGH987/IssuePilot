# Git & GitHub Collaboration Workflow for First-Time Contributors

A standardized, step-by-step Git guide designed to help first-time open-source contributors navigate forking, branch management, commit hygiene, and pull request submission without headaches.

---

## 1. Forking & Cloning

Open-source contributions typically use the **Fork and Pull** model:

1. **Fork the Repository**: Navigate to the target repository on GitHub and click the **Fork** button (top right).
2. **Clone Your Fork**:
   ```bash
   git clone https://github.com/<your-username>/<repository-name>.git
   cd <repository-name>
   ```
3. **Configure Upstream Remote**:
   Keep track of the original upstream project so you can sync incoming changes:
   ```bash
   git remote add upstream https://github.com/<original-owner>/<repository-name>.git
   git remote -v
   ```
   *Expected output: `origin` points to your fork, `upstream` points to the main repository.*

---

## 2. Syncing with Upstream

Before starting any new work or opening a PR, always pull the latest commits from `upstream/main` (or `upstream/master`):

```bash
# Fetch latest changes from the original repository
git fetch upstream

# Switch to your local main branch
git checkout main

# Rebase or merge upstream changes into your local main
git rebase upstream/main

# Push updated main to your personal GitHub fork
git push origin main
```

---

## 3. Creating a Focused Feature Branch

Never commit directly to `main`. Create an isolated feature branch named after your task or issue number:

```bash
# Naming format: <type>/<short-description> or <type>/issue-<number>
git checkout -b fix/issue-42-typo-config
```

Common branch naming prefixes:
- `feat/`: New feature or enhancement
- `fix/`: Bug fix
- `docs/`: Documentation updates
- `test/`: Adding or correcting tests

---

## 4. Conventional Commits Standard

Maintainers appreciate readable, structured commit histories. Follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format:
```
<type>(<optional scope>): <imperative description>

[optional body explaining 'why', not 'what']

[optional footer referencing issues]
```

### Commit Types:
| Type | Purpose | Example |
| :--- | :--- | :--- |
| `feat` | A new user-facing or developer feature | `feat(auth): add OAuth2 GitHub provider` |
| `fix` | A bug fix | `fix(parser): resolve null pointer on empty input` |
| `docs` | Documentation only changes | `docs(readme): clarify setup steps for Windows` |
| `test` | Adding missing tests or correcting existing tests | `test(harness): add unit tests for fallback logic` |
| `refactor` | Code change that neither fixes a bug nor adds a feature | `refactor(router): simplify request dispatching` |
| `chore` | Changes to build process, tooling, or dependencies | `chore(deps): bump requests from 2.31.0 to 2.32.0` |

### Committing Your Work:
```bash
git add path/to/changed_file.py
git commit -m "fix(cli): correct exit code when config file is missing"
```

---

## 5. Squash-Merge Hygiene & PR Cleanliness

1. **Keep Pull Requests Scoped**:
   One PR should solve one issue. Avoid grouping unrelated refactors or formatting changes with a bugfix.

2. **Self-Review Your Changes**:
   Before pushing, review your exact diff:
   ```bash
   git diff upstream/main
   ```

3. **Push to Your Fork**:
   ```bash
   git push -u origin fix/issue-42-typo-config
   ```

4. **Squash commits before or during merge**:
   If you have several small fixup commits (e.g., `fix typo`, `oops another typo`), squash them locally or rely on the repository's GitHub **Squash and Merge** button:
   ```bash
   # Optional interactive rebase of last 3 commits:
   git rebase -i HEAD~3
   ```

5. **Link the Issue in Your Pull Request**:
   In the PR description body on GitHub, write:
   ```markdown
   Closes #42
   # or
   Fixes #42
   ```
   GitHub will automatically link the PR to the issue and close the issue once the maintainers merge your PR.

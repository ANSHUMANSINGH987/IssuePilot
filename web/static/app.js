/**
 * IssuePilot (First-PR Navigator) — Frontend Controller
 * Modern Linear/Vercel-inspired client orchestrator.
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  const state = {
    selectedLanguage: "any",
    customLanguage: "",
    selectedDomain: "",
    selectedLevel: "first-timer",
    selectedEffort: "any",
    issues: [],
    loading: false,
    activeIssue: null,
    activeDossier: null,
  };

  // DOM Elements
  const modelStatusText = document.getElementById("modelStatusText");
  const languagePills = document.querySelectorAll("#languagePills .pill[data-lang], #languageOverflow .pill[data-lang]");
  const languageOverflow = document.getElementById("languageOverflow");
  const btnToggleLanguages = document.getElementById("btnToggleLanguages");
  const btnCustomLanguage = document.getElementById("btnCustomLanguage");
  const languageCustomEntry = document.getElementById("languageCustomEntry");
  const customLanguageInput = document.getElementById("customLanguageInput");
  const btnHideCustomLanguage = document.getElementById("btnHideCustomLanguage");
  const domainPills = document.querySelectorAll("#domainPills .pill");
  const experienceToggleBtns = document.querySelectorAll("#experienceToggle .toggle-btn");
  const effortPills = document.querySelectorAll("#effortPills .pill");
  const btnDiscoverIssues = document.getElementById("btnDiscoverIssues");
  const btnLoadDemo = document.getElementById("btnLoadDemo");
  const issuesGrid = document.getElementById("issuesGrid");
  const issuesCounter = document.getElementById("issuesCounter");
  const activeFilterTags = document.getElementById("activeFilterTags");

  // Drawer Elements
  const drawerOverlay = document.getElementById("drawerOverlay");
  const dossierDrawer = document.getElementById("dossierDrawer");
  const drawerCloseBtn = document.getElementById("drawerCloseBtn");
  const btnDownloadDossier = document.getElementById("btnDownloadDossier");
  const drawerEngineLabel = document.getElementById("drawerEngineLabel");
  const drawerTitle = document.getElementById("drawerTitle");
  const drawerMeta = document.getElementById("drawerMeta");
  const dossierSkeleton = document.getElementById("dossierSkeleton");
  const dossierContent = document.getElementById("dossierContent");
  const dossierSummary = document.getElementById("dossierSummary");
  const targetFilesList = document.getElementById("targetFilesList");
  const terminalCode = document.getElementById("terminalCode");
  const btnCopyTerminal = document.getElementById("btnCopyTerminal");
  const prChecklist = document.getElementById("prChecklist");
  const toastMessage = document.getElementById("toastMessage");

  // Check Backend Health
  async function checkHealth() {
    try {
      const res = await fetch("/api/health");
      if (res.ok) {
        const data = await res.json();
        const modelName = data.open_weight_model || "qwen2.5-coder:7b";
        const mode = data.mode === "live" ? "Live Inference" : "Smart Fallback Active";
        modelStatusText.textContent = `${modelName} • ${mode}`;
      } else {
        modelStatusText.textContent = "Offline Model Harness";
      }
    } catch {
      modelStatusText.textContent = "Offline Model Harness";
    }
  }

  // Toast Helper
  function showToast(message, isError = false) {
    toastMessage.textContent = message;
    toastMessage.classList.toggle("error", isError);
    toastMessage.classList.add("show");
    setTimeout(() => {
      toastMessage.classList.remove("show");
    }, 2500);
  }

  // Update Active Filter Tags
  function updateFilterTags() {
    const languageLabel = state.customLanguage || (state.selectedLanguage === "any" ? "ANY" : state.selectedLanguage.toUpperCase());
    const effortLabel = state.selectedEffort === "any" ? "ANY HORIZON" : state.selectedEffort.toUpperCase();
    activeFilterTags.innerHTML = `
      <span class="filter-tag">Lang: ${escapeHtml(languageLabel)}</span>
      ${state.selectedDomain ? `<span class="filter-tag">Domain: ${escapeHtml(state.selectedDomain)}</span>` : ""}
      <span class="filter-tag">Level: ${state.selectedLevel}</span>
      <span class="filter-tag">Effort: ${effortLabel}</span>
    `;
  }

  function selectedLanguageValue() {
    return state.customLanguage.trim() || (state.selectedLanguage === "any" ? "" : state.selectedLanguage);
  }

  // Render Skeletons in Grid
  function renderGridSkeletons(count = 3) {
    issuesGrid.innerHTML = Array.from({ length: count })
      .map(
        () => `
        <div class="skeleton-card">
          <div class="skeleton-line short"></div>
          <div class="skeleton-line full"></div>
          <div class="skeleton-line medium"></div>
          <div class="skeleton-box"></div>
        </div>
      `
      )
      .join("");
  }

  // Discover Issues via API
  async function fetchCandidateIssues() {
    state.loading = true;
    issuesCounter.textContent = "Scanning repositories...";
    renderGridSkeletons(3);

    try {
      const res = await fetch("/api/scan", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          language: selectedLanguageValue(),
          topic: state.selectedDomain || null,
          experience: state.selectedLevel,
          effort: state.selectedEffort === "any" ? null : state.selectedEffort,
          limit: 6,
        }),
      });

      if (!res.ok) {
        throw new Error(`Issue scan failed (${res.status})`);
      }

      const data = await res.json();
      state.issues = data.issues || [];
      renderIssuesGrid();
    } catch (err) {
      console.error("Scan error:", err);
      showToast(err.message || "Failed to fetch candidate issues.", true);
      issuesCounter.textContent = "Error scanning issues";
      issuesGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 2rem; color: var(--text-muted);">
          Failed to fetch candidate issues. Please try again.
        </div>
      `;
    } finally {
      state.loading = false;
    }
  }

  // Render Issue Cards
  function renderIssuesGrid() {
    if (!state.issues || state.issues.length === 0) {
      issuesCounter.textContent = "0 issues found";
      issuesGrid.innerHTML = `
        <div style="grid-column: 1 / -1; text-align: center; padding: 3rem; color: var(--text-secondary);">
          <p style="margin-bottom: 0.5rem; font-size: 1.1rem; font-weight: 600;">No matching candidate issues found</p>
          <p style="font-size: 0.85rem; color: var(--text-muted);">Try selecting another language or clear the domain filter.</p>
        </div>
      `;
      return;
    }

    issuesCounter.textContent = `${state.issues.length} candidate issues available`;

    issuesGrid.innerHTML = state.issues
      .map((issue) => {
        const labelsHtml = (issue.labels || [])
          .slice(0, 4)
          .map((lbl) => {
            const lower = lbl.toLowerCase();
            let extraClass = "";
            if (lower.includes("hacktoberfest")) extraClass = "hacktoberfest";
            else if (lower.includes("good first") || lower.includes("beginner")) extraClass = "good-first-issue";
            return `<span class="label-pill ${extraClass}">${escapeHtml(lbl)}</span>`;
          })
          .join("");

        const comments = issue.comments || 0;
        const availabilityBadge = comments <= 2 ? `Available: ${comments} comments` : `${comments} comments`;

        return `
          <div class="issue-card" data-issue-number="${issue.number}">
            <div>
              <div class="card-top">
                <span class="repo-badge">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M15 22v-4a4.8 4.8 0 0 0-1-3.5c3 0 6-2 6-5.5.08-1.25-.27-2.48-1-3.5.28-1.15.28-2.35 0-3.5 0 0-1 0-3 1.5-2.64-.5-5.36-.5-8 0C6 2 5 2 5 2c-.3 1.15-.3 2.35 0 3.5A5.403 5.403 0 0 0 4 9c0 3.5 3 5.5 6 5.5-.39.49-.68 1.05-.85 1.65-.17.6-.22 1.23-.15 1.85v4"/>
                    <path d="M9 18c-4.51 2-5-2-7-2"/>
                  </svg>
                  ${escapeHtml(issue.repo)}
                </span>
                <span class="comments-badge">${availabilityBadge}</span>
              </div>

              <a href="${issue.html_url}" target="_blank" rel="noreferrer" class="issue-title">
                #${issue.number} ${escapeHtml(issue.title)}
              </a>

              <p class="issue-body-preview">${escapeHtml(issue.body || "No issue description provided.")}</p>

              <div class="issue-labels">${labelsHtml}</div>
            </div>

            <div class="card-footer">
              <span class="issue-date">${formatDate(issue.created_at)}</span>
              <button class="btn-generate-dossier" data-repo="${issue.repo}" data-number="${issue.number}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/>
                  <polyline points="14 2 14 8 20 8"/>
                </svg>
                Generate Dossier
              </button>
            </div>
          </div>
        `;
      })
      .join("");

    // Attach click listeners to cards
    document.querySelectorAll(".btn-generate-dossier").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const repo = btn.getAttribute("data-repo");
        const number = parseInt(btn.getAttribute("data-number"), 10);
        const issue = state.issues.find((i) => i.repo === repo && i.number === number);
        if (issue) {
          openDossierDrawer(issue);
        }
      });
    });
  }

  // Open Drawer and Synthesize Dossier
  async function openDossierDrawer(issue) {
    state.activeIssue = issue;
    drawerOverlay.classList.add("active");
    dossierDrawer.classList.add("active");
    document.body.style.overflow = "hidden";

    drawerTitle.textContent = `#${issue.number} ${issue.title}`;
    drawerMeta.textContent = `${issue.repo} • Primary: ${(state.customLanguage || state.selectedLanguage).toUpperCase()}`;
    drawerEngineLabel.textContent = "Synthesizing Dossier...";

    dossierSkeleton.style.display = "block";
    dossierContent.style.display = "none";

    try {
      const res = await fetch("/api/dossier", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          repo: issue.repo,
          number: issue.number,
          title: issue.title,
          html_url: issue.html_url,
          body: issue.body,
          language: selectedLanguageValue(),
        }),
      });

      if (!res.ok) {
        throw new Error(`Dossier synthesis failed (${res.status})`);
      }

      const data = await res.json();
      state.activeDossier = data;
      renderDossierDetails(data, issue);
    } catch (err) {
      console.error("Dossier generation error:", err);
      showToast(err.message || "Failed to synthesize Onboarding Dossier.", true);
      drawerEngineLabel.textContent = "Synthesis Error";
      dossierSkeleton.style.display = "none";
      dossierContent.style.display = "block";
      dossierSummary.textContent = "Failed to synthesize Onboarding Dossier. Please try again.";
    }
  }

  // Render Detailed Dossier in Drawer
  function renderDossierDetails(data, issue) {
    const engine = data.engine || "Open-Weight Harness";
    const model = data.model || "qwen2.5-coder:7b";
    drawerEngineLabel.textContent = `Generated by ${model} (${engine})`;

    const repoAnalysis = data.repo_analysis || {};
    const stack = repoAnalysis.stack_indicators || {};
    const quickstart = repoAnalysis.suggested_quickstart || {};
    const repoName = issue.repo.split("/")[1] || issue.repo;
    const cleanSlug = issue.title.toLowerCase().replace(/[^a-z0-9]+/g, "-").slice(0, 30);
    const branchName = `fix/issue-${issue.number}-${cleanSlug}`;

    // 1. Executive Summary (Crisp 3 sentences)
    dossierSummary.textContent = `${issue.repo} is an open-source ${repoAnalysis.primary_language || state.selectedLanguage} repository with tests orchestrated via ${stack.test_runner || "standard test harness"}. This issue asks to resolve "${issue.title.slice(0, 75)}" without breaking existing regressions. Contributors should verify code changes locally and submit a clean PR following Conventional Commits.`;

    // 2. Target Files
    const targetDir = repoAnalysis.top_level_files?.find((f) => f.includes("src/") || f.includes(repoName.replace("-", "_") + "/")) || "src/";
    targetFilesList.innerHTML = `
      <div class="target-file-item">
        <span class="target-file-path">${targetDir}</span>
        <span class="target-file-desc">Core logic implementation</span>
      </div>
      <div class="target-file-item">
        <span class="target-file-path">tests/</span>
        <span class="target-file-desc">Add unit test covering #${issue.number}</span>
      </div>
      <div class="target-file-item">
        <span class="target-file-path">README.md / CONTRIBUTING.md</span>
        <span class="target-file-desc">Review setup & style guidelines</span>
      </div>
    `;

    // 3. Terminal Script
    const scriptCommands = `# 1. Clone fork and add upstream remote
git clone https://github.com/<your-username>/${repoName}.git
cd ${repoName}
git remote add upstream https://github.com/${issue.repo}.git

# 2. Install dependencies & tools
${quickstart.install || "pip install -e ."}

# 3. Create isolated feature branch
git checkout -b ${branchName}

# 4. Run baseline test suite
${quickstart.test || "pytest"}

# 5. Run static lint checks
${quickstart.lint || "ruff check ."}`;

    terminalCode.textContent = scriptCommands;

    // 4. PR Checklist
    prChecklist.innerHTML = `
      <li class="pr-checklist-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>Branch isolated on <code>${branchName}</code></span>
      </li>
      <li class="pr-checklist-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>Clean commit message: <code>git commit -m "fix(issue-${issue.number}): ${issue.title.slice(0, 45).toLowerCase()}"</code></span>
      </li>
      <li class="pr-checklist-item">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12"/>
        </svg>
        <span>PR description includes <code>Fixes #${issue.number}</code> to automatically link and close ticket</span>
      </li>
    `;

    dossierSkeleton.style.display = "none";
    dossierContent.style.display = "block";
  }

  // Close Drawer
  function closeDrawer() {
    drawerOverlay.classList.remove("active");
    dossierDrawer.classList.remove("active");
    document.body.style.overflow = "";
  }

  // Copy Terminal Script
  btnCopyTerminal.addEventListener("click", () => {
    const text = terminalCode.textContent;
    if (!text) return;

    navigator.clipboard.writeText(text).then(() => {
      showToast("Copied terminal sequence to clipboard!");
    }).catch(() => {
      showToast("Failed to copy automatically.");
    });
  });

  // Download Dossier as Markdown (.md)
  if (btnDownloadDossier) {
    btnDownloadDossier.addEventListener("click", () => {
      if (!state.activeIssue) return;
      const issueNum = state.activeIssue.number;
      let markdownContent = state.activeDossier?.dossier_markdown;

      if (!markdownContent) {
        markdownContent = `# First-PR Onboarding Dossier: #${issueNum} ${state.activeIssue.title}\n\n` +
          `> Target Repository: ${state.activeIssue.repo}\n` +
          `> Issue URL: ${state.activeIssue.html_url}\n\n` +
          `## Executive Architecture Summary\n${dossierSummary.textContent}\n\n` +
          `## Setup Script\n\`\`\`bash\n${terminalCode.textContent}\n\`\`\`\n`;
      }

      const blob = new Blob([markdownContent], { type: "text/markdown;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `first-pr-dossier-issue-${issueNum}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      showToast(`Downloaded first-pr-dossier-issue-${issueNum}.md`);
    });
  }

  // Event Listeners for Filters
  languagePills.forEach((pill) => {
    pill.addEventListener("click", () => {
      languagePills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.selectedLanguage = pill.getAttribute("data-lang");
      state.customLanguage = "";
      customLanguageInput.value = "";
      updateFilterTags();
      fetchCandidateIssues();
    });
  });

  btnToggleLanguages.addEventListener("click", () => {
    const expanded = !languageOverflow.hidden;
    languageOverflow.hidden = expanded;
    btnToggleLanguages.textContent = expanded ? "Show more languages..." : "Show fewer languages";
  });

  btnCustomLanguage.addEventListener("click", () => {
    languageCustomEntry.hidden = false;
    customLanguageInput.focus();
  });

  customLanguageInput.addEventListener("input", () => {
    state.customLanguage = customLanguageInput.value;
    languagePills.forEach((p) => p.classList.remove("active"));
    updateFilterTags();
  });

  customLanguageInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      fetchCandidateIssues();
    }
  });

  btnHideCustomLanguage.addEventListener("click", () => {
    state.customLanguage = "";
    customLanguageInput.value = "";
    languageCustomEntry.hidden = true;
    languagePills.forEach((p) => p.classList.toggle("active", p.getAttribute("data-lang") === state.selectedLanguage));
    updateFilterTags();
  });

  domainPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      domainPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.selectedDomain = pill.getAttribute("data-topic");
      updateFilterTags();
      fetchCandidateIssues();
    });
  });

  experienceToggleBtns.forEach((btn) => {
    btn.addEventListener("click", () => {
      experienceToggleBtns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      state.selectedLevel = btn.getAttribute("data-level");
      updateFilterTags();
      fetchCandidateIssues();
    });
  });

  effortPills.forEach((pill) => {
    pill.addEventListener("click", () => {
      effortPills.forEach((p) => p.classList.remove("active"));
      pill.classList.add("active");
      state.selectedEffort = pill.getAttribute("data-effort");
      updateFilterTags();
      fetchCandidateIssues();
    });
  });

  btnDiscoverIssues.addEventListener("click", () => {
    fetchCandidateIssues();
  });

  // Load Demo Profile Button (Quick preset for Hackathon evaluators)
  btnLoadDemo.addEventListener("click", () => {
    // Select Python
    languagePills.forEach((p) => {
      p.classList.toggle("active", p.getAttribute("data-lang") === "python");
    });
    state.selectedLanguage = "python";
    state.customLanguage = "";
    customLanguageInput.value = "";
    languageCustomEntry.hidden = true;

    // Select CLI
    domainPills.forEach((p) => {
      p.classList.toggle("active", p.getAttribute("data-topic") === "cli");
    });
    state.selectedDomain = "cli";

    // Select First Timer
    experienceToggleBtns.forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-level") === "first-timer");
    });
    state.selectedLevel = "first-timer";

    effortPills.forEach((p) => {
      p.classList.toggle("active", p.getAttribute("data-effort") === "any");
    });
    state.selectedEffort = "any";

    updateFilterTags();
    showToast("Loaded demo profile: Python + CLI Tools");
    fetchCandidateIssues();
  });

  // Drawer Close Listeners
  drawerCloseBtn.addEventListener("click", closeDrawer);
  drawerOverlay.addEventListener("click", closeDrawer);

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && dossierDrawer.classList.contains("active")) {
      closeDrawer();
    }
  });

  // Utilities
  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  function formatDate(isoStr) {
    if (!isoStr) return "";
    try {
      const d = new Date(isoStr);
      return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
    } catch {
      return "";
    }
  }

  // Initialization
  checkHealth();
  updateFilterTags();
  fetchCandidateIssues();
});

#!/usr/bin/env python3
"""
test_run.py - End-to-End Integration Test for IssuePilot Phase 2.

Executes the complete operational pipeline:
1. Scan GitHub for candidate beginner issues via scan_issues.py
2. Select top candidate issue
3. Analyze repository topology & developer workflows via analyze_repo.py
4. Synthesize step-by-step Onboarding Dossier via open-weight model harness
"""

import os
import sys
import argparse

# Reconfigure stdout/stderr for UTF-8 compatibility on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Ensure project root and scripts directory are in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "first-pr-navigator", "scripts")

for p in [PROJECT_ROOT, SCRIPTS_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from scan_issues import find_candidate_issues
from analyze_repo import analyze_github_repo
from harness.client import OpenWeightClient
from harness.dossier_synthesizer import DossierSynthesizer


def main():
    parser = argparse.ArgumentParser(description="End-to-End Test Run for IssuePilot.")
    parser.add_argument("--language", "-l", type=str, default="python", help="Language filter (default: python)")
    parser.add_argument("--repo", "-r", type=str, default=None, help="Target specific repository")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output markdown path")
    args = parser.parse_args()

    print("=" * 70)
    print("🚀 IssuePilot (First-PR Navigator) — End-to-End Pipeline Test")
    print("=" * 70)

    # 1. Candidate Issue Discovery
    print(f"\n[Step 1/4] Scanning candidate issues (Language: {args.language})...")
    issues = find_candidate_issues(language=args.language, limit=3, repo=args.repo)
    if not issues:
        print("❌ No candidate issues found.")
        sys.exit(1)

    print(f"Found {len(issues)} candidate issues:")
    for idx, iss in enumerate(issues, 1):
        print(f"  {idx}. [{iss.get('repo')}] #{iss.get('number')} - {iss.get('title')}")

    # Pick top candidate
    selected_issue = issues[0]
    target_repo = selected_issue.get("repo")
    print(f"\nSelected Candidate: #{selected_issue.get('number')} in '{target_repo}'")
    print(f"URL: {selected_issue.get('html_url')}")

    # 2. Repository Contextualization
    print(f"\n[Step 2/4] Contextualizing repository architecture for '{target_repo}'...")
    repo_analysis = analyze_github_repo(target_repo)
    stack = repo_analysis.get("stack_indicators", {})
    print(f"  • Primary Language: {repo_analysis.get('primary_language')}")
    print(f"  • Build System:     {stack.get('build_system')}")
    print(f"  • Test Runner:      {stack.get('test_runner')}")
    print(f"  • Default Branch:   {repo_analysis.get('default_branch')}")

    # 3. Model Harness Initialization
    print(f"\n[Step 3/4] Initializing Open-Weight Model Harness...")
    client = OpenWeightClient()
    print(f"  • API Base: {client.api_base}")
    print(f"  • Model:    {client.model}")
    server_online = client.is_server_available()
    print(f"  • Status:   {'ONLINE (Live Inference)' if server_online else 'OFFLINE (Fallback Engine Active)'}")

    # 4. Dossier Synthesis
    print(f"\n[Step 4/4] Synthesizing Onboarding Dossier...")
    synthesizer = DossierSynthesizer(client=client)
    result = synthesizer.synthesize(selected_issue, repo_analysis)

    dossier_text = result["dossier_markdown"]
    engine = result["engine"]
    print(f"✅ Dossier successfully synthesized via [{engine}]!")

    # Write output file
    output_path = args.output or os.path.join(PROJECT_ROOT, "output", f"dossier_issue_{selected_issue.get('number')}.md")
    dirname = os.path.dirname(output_path)
    if dirname:
        os.makedirs(dirname, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(dossier_text)

    print(f"📄 Saved Onboarding Dossier to: {output_path}")

    # Preview snippet
    print("\n" + "-" * 70)
    print("PREVIEW OF SYNTHESIZED DOSSIER (First 20 lines):")
    print("-" * 70)
    preview_lines = dossier_text.strip().split("\n")[:20]
    print("\n".join(preview_lines))
    print("-" * 70)
    print("✨ End-to-end execution completed successfully!")


if __name__ == "__main__":
    main()

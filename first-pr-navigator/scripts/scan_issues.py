#!/usr/bin/env python3
"""
scan_issues.py - GitHub Issue Candidate Discovery for First-PR Navigator.

Queries GitHub API for beginner-friendly, unassigned Hacktoberfest issues:
- State: open
- Assignee: none (unassigned)
- Labels: "good first issue", "help wanted", "hacktoberfest"
- Filter: language, keyword/topic, comment count (< 5)
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Any, Optional

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load local .env if present without requiring third-party libraries
def load_dotenv(filepath: str = ".env") -> None:
    if not os.path.exists(filepath):
        # Also check parent directory
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

MOCK_CANDIDATE_ISSUES = [
    {
        "id": 101,
        "number": 42,
        "title": "Add retry mechanism with exponential backoff to HTTP client",
        "repo": "psf/requests-toolbelt",
        "html_url": "https://github.com/psf/requests-toolbelt/issues/42",
        "url": "https://github.com/psf/requests-toolbelt/issues/42",
        "author": "sigmaview",
        "labels": ["good first issue", "hacktoberfest", "help wanted"],
        "comments": 2,
        "created_at": "2026-09-28T10:14:00Z",
        "language": "python",
        "domain": "systems",
        "effort": "standard",
        "body": "The current HTTP adapter fails immediately on 503 Service Unavailable without retrying. We should implement an optional MaxRetry wrapper that respects the Retry-After header with exponential backoff.",
    },
    {
        "id": 102,
        "number": 88,
        "title": "Improve CLI error message when configuration file is malformed",
        "repo": "fastapi/fastapi-cli",
        "html_url": "https://github.com/fastapi/fastapi-cli/issues/88",
        "url": "https://github.com/fastapi/fastapi-cli/issues/88",
        "author": "dev-guru",
        "labels": ["good first issue", "help wanted"],
        "comments": 1,
        "created_at": "2026-09-30T14:20:00Z",
        "language": "python",
        "domain": "cli",
        "effort": "quick",
        "body": "When fastapi.json has a syntax error, the CLI currently dumps a raw JSONDecodeError traceback. We should catch this exception and display a clean, friendly error message pointing to the line number.",
    },
    {
        "id": 103,
        "number": 154,
        "title": "Add dark mode toggle support in navigation component",
        "repo": "shadcn/ui-components",
        "html_url": "https://github.com/shadcn/ui-components/issues/154",
        "url": "https://github.com/shadcn/ui-components/issues/154",
        "author": "frontend-pro",
        "labels": ["good first issue", "hacktoberfest"],
        "comments": 3,
        "created_at": "2026-09-29T18:45:00Z",
        "language": "typescript",
        "domain": "frontend",
        "effort": "standard",
        "body": "The top navbar does not sync with the user's system dark mode preference or provide a manual toggle icon button. Needs a responsive theme switcher component.",
    }
]

MOCK_CANDIDATE_ISSUES.extend([
    {
        "id": 104,
        "number": 61,
        "title": "Add a retrieval example for the agent toolkit",
        "repo": "openai/openai-cookbook",
        "html_url": "https://github.com/openai/openai-cookbook/issues/61",
        "url": "https://github.com/openai/openai-cookbook/issues/61",
        "author": "mlh-mentor",
        "labels": ["good first issue", "documentation", "ai"],
        "comments": 2,
        "created_at": "2026-09-27T11:00:00Z",
        "language": "python",
        "domain": "ai",
        "effort": "deep-dive",
        "body": "Document a small retrieval-augmented generation example for students building AI agents.",
    },
    {
        "id": 105,
        "number": 73,
        "title": "Improve local container development instructions",
        "repo": "docker/awesome-compose",
        "html_url": "https://github.com/docker/awesome-compose/issues/73",
        "url": "https://github.com/docker/awesome-compose/issues/73",
        "author": "cloud-guide",
        "labels": ["good first issue", "help wanted", "devops"],
        "comments": 1,
        "created_at": "2026-09-26T09:30:00Z",
        "language": "yaml",
        "domain": "cloud",
        "effort": "standard",
        "body": "Clarify the Docker Compose steps and health checks for local cloud-native development.",
    },
    {
        "id": 106,
        "number": 29,
        "title": "Add onboarding notes for the Kotlin mobile sample",
        "repo": "android/nowinandroid",
        "html_url": "https://github.com/android/nowinandroid/issues/29",
        "url": "https://github.com/android/nowinandroid/issues/29",
        "author": "mobile-student",
        "labels": ["good first issue", "help wanted", "android"],
        "comments": 2,
        "created_at": "2026-09-25T16:20:00Z",
        "language": "kotlin",
        "domain": "mobile",
        "effort": "quick",
        "body": "Add a concise setup note for running the Kotlin mobile sample on an emulator.",
    },
    {
        "id": 107,
        "number": 18,
        "title": "Document the secure password reset flow",
        "repo": "owasp/www-project-top-ten",
        "html_url": "https://github.com/owasp/www-project-top-ten/issues/18",
        "url": "https://github.com/owasp/www-project-top-ten/issues/18",
        "author": "security-writer",
        "labels": ["good first issue", "documentation", "cybersecurity"],
        "comments": 1,
        "created_at": "2026-09-24T12:10:00Z",
        "language": "markdown",
        "domain": "docs",
        "effort": "standard",
        "body": "Improve the technical writing around secure password reset implementation and threat modeling.",
    },
    {
        "id": 108,
        "number": 34,
        "title": "Add a Zig systems programming example",
        "repo": "zigtools/zls",
        "html_url": "https://github.com/zigtools/zls/issues/34",
        "url": "https://github.com/zigtools/zls/issues/34",
        "author": "systems-student",
        "labels": ["good first issue", "help wanted", "systems"],
        "comments": 3,
        "created_at": "2026-09-23T08:45:00Z",
        "language": "zig",
        "domain": "systems",
        "effort": "deep-dive",
        "body": "Add a focused Zig example showing how to inspect symbols in a systems project.",
    },
])

LANGUAGE_QUERY_ALIASES = {
    "c#": '"C#"',
    "csharp": '"C#"',
    "cpp": '"C++"',
    "c++": '"C++"',
}

DOMAIN_QUERY_ALIASES = {
    "ai": "(topic:ai OR topic:machine-learning OR topic:llm OR topic:agents)",
    "agents": "(topic:ai OR topic:machine-learning OR topic:llm OR topic:agents)",
    "cybersecurity": "(topic:security OR topic:infosec)",
    "security": "(topic:security OR topic:infosec)",
    "docs": '(label:"documentation" OR label:"docs")',
    "documentation": '(label:"documentation" OR label:"docs")',
    "web": "(topic:web OR topic:api)",
    "frontend": "(topic:frontend OR topic:ui)",
    "cloud": "(topic:cloud OR topic:devops)",
    "devops": "(topic:cloud OR topic:devops)",
    "mobile": "(topic:mobile OR topic:android OR topic:ios)",
}


def build_search_query(
    language: Optional[str] = None,
    topic: Optional[str] = None,
    labels: Optional[List[str]] = None,
    max_comments: int = 5,
    repo: Optional[str] = None,
    effort: Optional[str] = None,
) -> str:
    """Constructs a targeted GitHub issue search query."""
    parts = ["is:issue", "is:open", "no:assignee"]

    if max_comments > 0:
        parts.append(f"comments:<{max_comments}")

    if repo:
        parts.append(f"repo:{repo}")

    normalized_language = (language or "").strip().lower()
    if normalized_language and normalized_language not in {"any", "*"}:
        language_query = LANGUAGE_QUERY_ALIASES.get(normalized_language, language.strip())
        parts.append(f"language:{language_query}")

    normalized_topic = (topic or "").strip().lower()
    if normalized_topic and normalized_topic not in {"any", "all", "all domains", "*"}:
        parts.append(DOMAIN_QUERY_ALIASES.get(normalized_topic, topic.strip()))

    # Label qualification
    if labels:
        label_clauses = [f'label:"{lbl}"' for lbl in labels]
        parts.append("(" + " OR ".join(label_clauses) + ")")
    else:
        parts.append('(label:"good first issue" OR label:"help wanted" OR label:"hacktoberfest")')

    return " ".join(parts)


def find_candidate_issues(
    language: Optional[str] = None,
    topic: Optional[str] = None,
    limit: int = 5,
    max_comments: int = 5,
    repo: Optional[str] = None,
    token: Optional[str] = None,
    use_mock_fallback: bool = True,
    effort: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Queries GitHub Search API for candidate beginner issues.
    Falls back to curated mock candidate set if rate limited or offline.
    """
    token = token or os.environ.get("GITHUB_TOKEN")
    query = build_search_query(
        language=language,
        topic=topic,
        max_comments=max_comments,
        repo=repo,
        effort=effort,
    )

    url = f"https://api.github.com/search/issues?q={urllib.parse.quote(query)}&sort=created&order=desc&per_page={limit}"
    
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "IssuePilot-FirstPRNavigator/0.1.0",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            items = data.get("items", [])
            
            candidates = []
            for item in items[:limit]:
                # Extract repo 'owner/repo' from repository_url
                repo_url = item.get("repository_url", "")
                repo_full_name = "/".join(repo_url.split("/")[-2:]) if repo_url else "unknown/repo"
                
                body_text = item.get("body") or ""
                # Clean and truncate body for concise context
                summary_body = body_text.strip()
                if len(summary_body) > 1000:
                    summary_body = summary_body[:1000] + "... [truncated]"

                candidates.append({
                    "id": item.get("id"),
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "repo": repo_full_name,
                    "html_url": item.get("html_url"),
                    "url": item.get("html_url"),
                    "url": item.get("html_url"),
                    "author": (item.get("user") or {}).get("login", "unknown"),
                    "labels": [lbl.get("name") for lbl in item.get("labels", []) if isinstance(lbl, dict)],
                    "comments": item.get("comments", 0),
                    "created_at": item.get("created_at"),
                    "language": language or "any",
                    "domain": topic or "any",
                    "effort": effort or "any",
                    "body": summary_body,
                })
            
            if candidates:
                return candidates

    except urllib.error.HTTPError as e:
        sys.stderr.write(f"[WARN] GitHub API HTTP error: {e.code} - {e.reason}\n")
        if e.code in (401, 403):
            sys.stderr.write("[HINT] Rate limit reached. Provide GITHUB_TOKEN in .env for authenticated requests.\n")
    except Exception as e:
        sys.stderr.write(f"[WARN] Failed to reach GitHub API: {e}\n")

    if use_mock_fallback:
        sys.stderr.write("[INFO] Using verified candidate issue fixtures for local development.\n")
        # Filter mock candidates by language if specified.
        normalized_language = (language or "").strip().lower()
        candidates = MOCK_CANDIDATE_ISSUES
        if normalized_language and normalized_language not in {"any", "*"}:
            candidates = [
                candidate for candidate in candidates
                if candidate.get("language", "").lower() == normalized_language
            ]

        normalized_topic = (topic or "").strip().lower()
        if normalized_topic and normalized_topic not in {"any", "all", "all domains", "*"}:
            topic_text = normalized_topic
            candidates = [
                candidate for candidate in candidates
                if topic_text in " ".join([
                    candidate.get("domain", "").lower(),
                    *(label.lower() for label in candidate.get("labels", [])),
                    candidate.get("title", "").lower(),
                    candidate.get("body", "").lower(),
                ])
            ]

        normalized_effort = (effort or "").strip().lower()
        if normalized_effort and normalized_effort not in {"any", "*"}:
            candidates = [
                candidate for candidate in candidates
                if candidate.get("effort", "").lower() == normalized_effort
            ]

        return [dict(candidate, url=candidate.get("html_url")) for candidate in candidates[:limit]]

    return []


def main():
    parser = argparse.ArgumentParser(description="Scan GitHub for beginner-friendly Hacktoberfest issues.")
    parser.add_argument("--language", "-l", type=str, default=None, help="Language filter (e.g. python, typescript, go)")
    parser.add_argument("--topic", "-t", type=str, default=None, help="Topic or keyword filter (e.g. cli, fastapi)")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Maximum number of issues to return (default: 5)")
    parser.add_argument("--max-comments", type=int, default=5, help="Maximum comment threshold (default: 5)")
    parser.add_argument("--repo", "-r", type=str, default=None, help="Optional specific repository (owner/repo)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Optional output JSON file path")
    parser.add_argument("--no-mock", action="store_true", help="Disable mock fallback when API calls fail")

    args = parser.parse_args()

    results = find_candidate_issues(
        language=args.language,
        topic=args.topic,
        limit=args.limit,
        max_comments=args.max_comments,
        repo=args.repo,
        use_mock_fallback=not args.no_mock,
    )

    json_output = json.dumps(results, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(json_output)
        print(f"Candidate issues written to {args.output}")
    else:
        print(json_output)


if __name__ == "__main__":
    main()

"""Shared helpers for the AI CI scripts (Python stdlib only).

The AI itself runs in the workflow via anthropics/claude-code-action and returns
structured JSON; these helpers only collect inputs and post results to GitHub.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request

GITHUB_API = os.getenv("GITHUB_API_URL", "https://api.github.com")
REPO = os.getenv("GITHUB_REPOSITORY", "")


def log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def sh(*args: str, check: bool = True) -> str:
    result = subprocess.run(args, capture_output=True, text=True)
    if check and result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def truncate(text: str, limit: int) -> str:
    """Keep head + tail of long logs/diffs."""
    if len(text) <= limit:
        return text
    head = limit // 3
    return text[:head] + f"\n\n... [truncated {len(text) - limit} chars] ...\n\n" + text[-(limit - head):]


def set_output(name: str, value: str) -> None:
    path = os.getenv("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")
    log(f"output {name}={value}")


def write_summary(markdown: str) -> None:
    path = os.getenv("GITHUB_STEP_SUMMARY")
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(markdown + "\n")
    else:
        print(markdown)


def gh_api(method: str, path: str, payload: dict | None = None):
    url = path if path.startswith("http") else f"{GITHUB_API}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN', '')}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else None


def find_comment(pr: int | str, marker: str) -> dict | None:
    comments = gh_api("GET", f"/repos/{REPO}/issues/{pr}/comments?per_page=100") or []
    for c in reversed(comments):
        if marker in (c.get("body") or ""):
            return c
    return None


def upsert_comment(pr: int | str, marker: str, body: str) -> None:
    """Create or update a single 'sticky' bot comment identified by an HTML marker."""
    body = f"{marker}\n{body}"
    existing = find_comment(pr, marker)
    if existing:
        gh_api("PATCH", f"/repos/{REPO}/issues/comments/{existing['id']}", {"body": body})
        log(f"Updated comment {existing['html_url']}")
    else:
        created = gh_api("POST", f"/repos/{REPO}/issues/{pr}/comments", {"body": body})
        log(f"Created comment {created['html_url']}")

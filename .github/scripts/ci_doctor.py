#!/usr/bin/env python3
"""AI CI Doctor: when the CI workflow fails, read the failed logs, explain the
root cause and suggest a fix as a comment on the PR.

Usage:
  ci_doctor.py             diagnose a failed run
  ci_doctor.py --resolved  CI is green again -> mark the old diagnosis as resolved
"""

from __future__ import annotations

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ai  # noqa: E402

MARKER = "<!-- ai-ci-doctor -->"

SYSTEM = """You are a CI troubleshooting expert for Flutter/Dart projects (flutter analyze,
flutter test, pub, Android Gradle builds, iOS Xcode/CocoaPods builds). Given failed CI logs and the PR diff, find the ROOT CAUSE.
Do not just repeat the error; explain WHY it happens and point to the exact code change that
caused it when possible. Write in Vietnamese, keep code identifiers as-is.

Return JSON:
{
  "category": "test_failure|compile_error|lint|dependency|build|infra|flaky",
  "title": "one-line diagnosis",
  "root_cause": "2-4 sentences",
  "failing": ["test names / files that failed"],
  "suggested_fix": "concrete steps, may include a short code block in markdown",
  "confidence": "high|medium|low"
}"""

ANSI = re.compile(r"\x1b\[[0-9;]*[A-Za-z]")
TIMESTAMP = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z ")


def find_pr(sha: str) -> str:
    pr = os.getenv("PR_NUMBER", "").strip()
    if pr:
        return pr
    try:
        pulls = ai.gh_api("GET", f"/repos/{ai.REPO}/commits/{sha}/pulls") or []
        return str(pulls[0]["number"]) if pulls else ""
    except Exception as e:  # noqa: BLE001
        ai.log(f"Could not look up PR: {e}")
        return ""


def resolved() -> int:
    pr = find_pr(os.environ["HEAD_SHA"])
    if pr and ai.find_comment(pr, MARKER):
        ai.upsert_comment(pr, MARKER, "## 🩺 AI CI Doctor\n\n✅ CI đã xanh trở lại — chẩn đoán trước đã được xử lý.")
    return 0


def main() -> int:
    if "--resolved" in sys.argv:
        return resolved()

    run_id, sha = os.environ["RUN_ID"], os.environ["HEAD_SHA"]
    logs = ai.sh("gh", "run", "view", run_id, "--repo", ai.REPO, "--log-failed", check=False)
    logs = TIMESTAMP.sub("", ANSI.sub("", logs))
    if not logs.strip():
        ai.log("No failed logs found.")
        return 0

    pr = find_pr(sha)
    diff = ai.sh("gh", "pr", "diff", pr, "--repo", ai.REPO, check=False) if pr else ""
    prompt = (
        "## Failed CI logs (tail)\n```\n" + ai.truncate(logs, 12000) + "\n```\n\n"
        "## PR diff\n```diff\n" + ai.truncate(diff, 6000) + "\n```"
    )
    try:
        d = ai.chat_json(SYSTEM, prompt)
    except Exception as e:  # noqa: BLE001
        ai.log(str(e))
        return 0

    run_url = f"https://github.com/{ai.REPO}/actions/runs/{run_id}"
    failing = "\n".join(f"- `{x}`" for x in d.get("failing") or []) or "- (không xác định)"
    body = (
        f"## 🩺 AI CI Doctor — CI failed\n\n"
        f"**{d.get('title', '')}**  \n"
        f"Loại lỗi: `{d.get('category', '?')}` · Độ tin cậy: `{d.get('confidence', '?')}` · [Xem log]({run_url})\n\n"
        f"### Nguyên nhân\n{d.get('root_cause', '')}\n\n"
        f"### Đang fail\n{failing}\n\n"
        f"### Cách sửa đề xuất\n{d.get('suggested_fix', '')}"
        + ai.footer()
    )
    ai.write_summary(body)
    if pr:
        ai.upsert_comment(pr, MARKER, body)
    return 0


if __name__ == "__main__":
    sys.exit(main())

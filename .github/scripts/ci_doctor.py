#!/usr/bin/env python3
"""AI CI Doctor helper.

  ci_doctor.py --collect   save failed logs + PR diff to .ci-doctor/ for Claude, output PR number
  ci_doctor.py             render Claude's diagnosis (DOCTOR_JSON) as a sticky PR comment
  ci_doctor.py --resolved  CI is green again -> mark the old diagnosis as resolved
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ai  # noqa: E402

MARKER = "<!-- ai-ci-doctor -->"
OUT_DIR = ".ci-doctor"
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


def collect() -> int:
    run_id, sha = os.environ["RUN_ID"], os.environ["HEAD_SHA"]
    logs = ai.sh("gh", "run", "view", run_id, "--repo", ai.REPO, "--log-failed", check=False)
    logs = TIMESTAMP.sub("", ANSI.sub("", logs))
    pr = find_pr(sha)
    diff = ai.sh("gh", "pr", "diff", pr, "--repo", ai.REPO, check=False) if pr else ""
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/failed.log", "w", encoding="utf-8") as f:
        f.write(ai.truncate(logs, 60000) or "(no failed logs found)")
    with open(f"{OUT_DIR}/pr.diff", "w", encoding="utf-8") as f:
        f.write(ai.truncate(diff, 40000) or "(no PR diff)")
    ai.set_output("pr", pr)
    return 0


def resolved() -> int:
    pr = find_pr(os.environ["HEAD_SHA"])
    if pr and ai.find_comment(pr, MARKER):
        ai.upsert_comment(pr, MARKER, "## 🩺 AI CI Doctor\n\n✅ CI đã xanh trở lại — chẩn đoán trước đã được xử lý.")
    return 0


def post() -> int:
    raw = os.getenv("DOCTOR_JSON", "").strip()
    try:
        d = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        d = None
    if not isinstance(d, dict):
        ai.log("Claude returned no diagnosis (missing token / quota / error). Skipping.")
        return 0

    run_url = f"https://github.com/{ai.REPO}/actions/runs/{os.environ['RUN_ID']}"
    failing = "\n".join(f"- `{x}`" for x in d.get("failing") or []) or "- (không xác định)"
    body = (
        f"## 🩺 AI CI Doctor — CI failed\n\n"
        f"**{d.get('title', '')}**  \n"
        f"Loại lỗi: `{d.get('category', '?')}` · Độ tin cậy: `{d.get('confidence', '?')}` · [Xem log]({run_url})\n\n"
        f"### Nguyên nhân\n{d.get('root_cause', '')}\n\n"
        f"### Đang fail\n{failing}\n\n"
        f"### Cách sửa đề xuất\n{d.get('suggested_fix', '')}"
        "\n\n> 🛠️ Đồng ý với chẩn đoán thì comment `@claude fix theo chẩn đoán CI Doctor`."
        "\n\n---\n<sub>🤖 Claude Code · AI có thể sai — hãy kiểm tra trước khi áp dụng.</sub>"
    )
    ai.write_summary(body)
    pr = os.getenv("PR_NUMBER", "").strip()
    if pr:
        ai.upsert_comment(pr, MARKER, body)
    return 0


if __name__ == "__main__":
    if "--collect" in sys.argv:
        sys.exit(collect())
    if "--resolved" in sys.argv:
        sys.exit(resolved())
    sys.exit(post())

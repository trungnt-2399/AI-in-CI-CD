#!/usr/bin/env python3
"""AI CI Doctor helper — diagnoses failed CI (PR) and CD (mobile build) runs.

  ci_doctor.py --collect   save failed logs + diff to .ci-doctor/ for Claude, output PR number
  ci_doctor.py             post Claude's diagnosis (DOCTOR_JSON):
                             - run from a PR      -> sticky comment on the PR
                             - otherwise (CD/main) -> open/update a GitHub issue for that branch
  ci_doctor.py --resolved  run is green again -> mark PR comment resolved / close the issue
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

WORKFLOW = os.getenv("WORKFLOW_NAME", "CI")
BRANCH = os.getenv("HEAD_BRANCH", "")
EVENT = os.getenv("RUN_EVENT", "")


def issue_marker() -> str:
    return f"<!-- ai-ci-doctor-issue:{WORKFLOW}:{BRANCH} -->"


def find_pr() -> str:
    # Chỉ gắn với PR khi run được kích hoạt BỞI PR. Run trên release/main không comment
    # vào PR cũ (đã merge) có chứa cùng commit.
    if EVENT != "pull_request":
        return ""
    return os.getenv("PR_NUMBER", "").strip()


def find_issue() -> dict | None:
    issues = ai.gh_api("GET", f"/repos/{ai.REPO}/issues?state=open&per_page=100") or []
    for i in issues:
        if "pull_request" not in i and issue_marker() in (i.get("body") or ""):
            return i
    return None


def collect() -> int:
    run_id = os.environ["RUN_ID"]
    logs = ai.sh("gh", "run", "view", run_id, "--repo", ai.REPO, "--log-failed", check=False)
    logs = TIMESTAMP.sub("", ANSI.sub("", logs))
    pr = find_pr()
    if pr:
        diff = ai.sh("gh", "pr", "diff", pr, "--repo", ai.REPO, check=False)
    else:  # CD / push: show the latest commits on that branch
        diff = ai.sh("git", "-C", "pr", "log", "-n", "5", "--no-merges", "-p", "--stat", check=False)
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/failed.log", "w", encoding="utf-8") as f:
        f.write(ai.truncate(logs, 60000) or "(no failed logs found)")
    with open(f"{OUT_DIR}/pr.diff", "w", encoding="utf-8") as f:
        f.write(ai.truncate(diff, 40000) or "(no diff)")
    ai.set_output("pr", pr)
    return 0


def resolved() -> int:
    pr = find_pr()
    if pr:
        if ai.find_comment(pr, MARKER):
            ai.upsert_comment(pr, MARKER, "## 🩺 AI CI Doctor\n\n✅ CI đã xanh trở lại — chẩn đoán trước đã được xử lý.")
        return 0
    issue = find_issue()
    if issue:
        n = issue["number"]
        ai.gh_api("POST", f"/repos/{ai.REPO}/issues/{n}/comments",
                  {"body": f"✅ `{WORKFLOW}` trên `{BRANCH}` đã chạy thành công trở lại — đóng issue."})
        ai.gh_api("PATCH", f"/repos/{ai.REPO}/issues/{n}", {"state": "closed", "state_reason": "completed"})
        ai.log(f"Closed issue #{n}")
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
        f"## 🩺 AI CI Doctor — `{WORKFLOW}` failed\n\n"
        f"**{d.get('title', '')}**  \n"
        f"Nhánh: `{BRANCH}` · Loại lỗi: `{d.get('category', '?')}` · "
        f"Độ tin cậy: `{d.get('confidence', '?')}` · [Xem log]({run_url})\n\n"
        f"### Nguyên nhân\n{d.get('root_cause', '')}\n\n"
        f"### Đang fail\n{failing}\n\n"
        f"### Cách sửa đề xuất\n{d.get('suggested_fix', '')}"
        "\n\n---\n<sub>🤖 Claude Code · AI có thể sai — hãy kiểm tra trước khi áp dụng.</sub>"
    )
    ai.write_summary(body)

    pr = os.getenv("PR_NUMBER", "").strip()
    if pr:
        hint = "\n\n> 🛠️ Đồng ý với chẩn đoán thì comment `@claude fix theo chẩn đoán CI Doctor`."
        ai.upsert_comment(pr, MARKER, body + hint)
        return 0

    # Không có PR (CD build trên release/*, push main) -> mở/cập nhật issue để team thấy.
    title = f"🚨 {WORKFLOW} failed trên {BRANCH}: {d.get('title', '')}"[:200]
    issue_body = f"{issue_marker()}\n{body}"
    issue = find_issue()
    if issue:
        ai.gh_api("PATCH", f"/repos/{ai.REPO}/issues/{issue['number']}", {"title": title, "body": issue_body})
        ai.log(f"Updated issue {issue['html_url']}")
    else:
        created = ai.gh_api("POST", f"/repos/{ai.REPO}/issues", {"title": title, "body": issue_body})
        ai.log(f"Created issue {created['html_url']}")
    return 0


if __name__ == "__main__":
    if "--collect" in sys.argv:
        sys.exit(collect())
    if "--resolved" in sys.argv:
        sys.exit(resolved())
    sys.exit(post())

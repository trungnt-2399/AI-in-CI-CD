#!/usr/bin/env python3
"""Render Claude's structured review as one sticky PR comment.

Input: REVIEW_JSON (structured_output from claude-code-action).
Fails the check when there are Critical findings (FAIL_ON_CRITICAL=true) -> merge gate.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ai  # noqa: E402

MARKER = "<!-- ai-review -->"
SEVERITY_ICON = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "🔵"}
ORDER = ["critical", "major", "minor", "info"]
WARN_START, WARN_END = "<!-- warn -->", "<!-- /warn -->"


def render(result: dict) -> tuple[str, int]:
    findings = result.get("findings") or []
    findings.sort(key=lambda f: ORDER.index(f.get("severity")) if f.get("severity") in ORDER else 9)
    counts = {s: sum(1 for f in findings if f.get("severity") == s) for s in ORDER}

    lines = ["## 🤖 AI Code Review (Claude)", "", f"**Tóm tắt:** {result.get('summary', '')}", ""]
    lines.append(" · ".join(f"{SEVERITY_ICON[s]} {s.title()}: **{counts[s]}**" for s in ORDER))
    lines.append("")
    if not findings:
        lines.append("✅ Không phát hiện vấn đề đáng kể.")
    for f in findings:
        sev = f.get("severity", "info")
        loc = f"`{f.get('file', '?')}`" + (f":{f['line']}" if f.get("line") else "")
        lines.append(f"### {SEVERITY_ICON.get(sev, '🔵')} {sev.title()} — {loc}")
        lines.append(f.get("message", ""))
        if f.get("suggestion"):
            lines.append(f"\n> 💡 {f['suggestion']}")
        lines.append("")
    if counts["critical"]:
        lines.append("❌ **Có lỗi Critical → check `AI Review` fail, cần fix trước khi merge.**")
    hint = ("\n\n> 🛠️ Đồng ý với finding nào thì comment, ví dụ: `@claude fix các lỗi Critical` "
            "— Claude sẽ sửa trên nhánh này, chạy test rồi push commit để bạn review.") if findings else ""
    footer = hint + ("\n\n---\n<sub>🤖 Claude Code · rules: `.github/ai-review-rules.md` · "
                     "AI có thể sai — người review vẫn là người quyết định.</sub>")
    return "\n".join(lines) + footer, counts["critical"]


def main() -> int:
    pr = os.environ["PR_NUMBER"]
    raw = os.getenv("REVIEW_JSON", "").strip()
    try:
        result = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        result = None
    sha = os.getenv("HEAD_SHA", "")[:7]
    if not isinstance(result, dict):
        msg = (f"⚠️ Lần review cho commit `{sha}` bị lỗi (token, quota hoặc mạng — xem log Actions). "
               "Bỏ qua (fail-open).")
        ai.log(msg)
        existing = ai.find_comment(pr, MARKER)
        if existing:
            # Giữ nguyên kết quả review trước, chỉ thay dòng cảnh báo ở đầu.
            old = existing["body"].replace(MARKER, "", 1).split(WARN_END, 1)[-1].strip()
            ai.upsert_comment(pr, MARKER, f"{WARN_START}\n> {msg}\n{WARN_END}\n\n{old}")
        else:
            ai.upsert_comment(pr, MARKER, f"## 🤖 AI Code Review (Claude)\n\n{msg}")
        return 0

    body, critical = render(result)
    body = body.replace("## 🤖 AI Code Review (Claude)", f"## 🤖 AI Code Review (Claude) — commit `{sha}`", 1)
    ai.upsert_comment(pr, MARKER, body)
    ai.write_summary(body)
    if critical and os.getenv("FAIL_ON_CRITICAL", "true") == "true":
        ai.log(f"{critical} critical finding(s) -> failing the check.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

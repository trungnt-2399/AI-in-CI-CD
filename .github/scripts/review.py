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
    footer = ("\n\n---\n<sub>🤖 Claude Code · rules: `.github/ai-review-rules.md` · "
              "AI có thể sai — người review vẫn là người quyết định.</sub>")
    return "\n".join(lines) + footer, counts["critical"]


def main() -> int:
    pr = os.environ["PR_NUMBER"]
    raw = os.getenv("REVIEW_JSON", "").strip()
    try:
        result = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        result = None
    if not isinstance(result, dict):
        msg = "⚠️ Claude không trả về kết quả (thiếu secret `CLAUDE_CODE_OAUTH_TOKEN`, hết quota hoặc lỗi mạng). Bỏ qua (fail-open)."
        ai.log(msg)
        ai.upsert_comment(pr, MARKER, f"## 🤖 AI Code Review (Claude)\n\n{msg}")
        return 0

    body, critical = render(result)
    ai.upsert_comment(pr, MARKER, body)
    ai.write_summary(body)
    if critical and os.getenv("FAIL_ON_CRITICAL", "true") == "true":
        ai.log(f"{critical} critical finding(s) -> failing the check.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

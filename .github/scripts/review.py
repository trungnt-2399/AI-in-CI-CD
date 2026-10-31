#!/usr/bin/env python3
"""AI code review for a pull request.

Posts one sticky comment on the PR and fails the check when the AI finds
Critical issues (FAIL_ON_CRITICAL=true) -> works as a merge gate.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ai  # noqa: E402

MARKER = "<!-- ai-review -->"
SEVERITY_ICON = {"critical": "🔴", "major": "🟠", "minor": "🟡", "info": "🔵"}

SYSTEM = """You are a senior Flutter/Dart reviewer on a team at Sun*.
Review ONLY the changed lines in the diff. Be concise and concrete; no praise, no style nits
that `dart format` / `flutter analyze` already catch. Write messages in Vietnamese.

Team rules (follow strictly, they define severity):
{rules}

Return JSON:
{{
  "summary": "1-2 sentences: what this PR does",
  "verdict": "approve" | "request_changes" | "comment",
  "findings": [
    {{"severity": "critical|major|minor|info", "file": "path", "line": 0,
      "message": "what is wrong and why", "suggestion": "short fix or code"}}
  ]
}}
Return an empty findings list if the diff is fine."""


def render(result: dict) -> tuple[str, int]:
    findings = result.get("findings") or []
    order = ["critical", "major", "minor", "info"]
    findings.sort(key=lambda f: order.index(f.get("severity", "info")) if f.get("severity") in order else 9)
    counts = {s: sum(1 for f in findings if f.get("severity") == s) for s in order}

    lines = ["## 🤖 AI Code Review", "", f"**Tóm tắt:** {result.get('summary', '')}", ""]
    lines.append(" · ".join(f"{SEVERITY_ICON[s]} {s.title()}: **{counts[s]}**" for s in order))
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
    return "\n".join(lines) + ai.footer(), counts["critical"]


def main() -> int:
    pr = os.environ["PR_NUMBER"]
    base, head = os.environ["BASE_SHA"], os.environ["HEAD_SHA"]
    diff = ai.sh("git", "diff", "--unified=3", f"{base}...{head}", "--",
                 ".", ":(exclude)pubspec.lock", ":(exclude)**/*.g.dart", ":(exclude)**/*.freezed.dart")
    if not diff.strip():
        ai.log("Empty diff, nothing to review.")
        return 0

    rules = ai.read_file(".github/ai-review-rules.md", "(no extra rules)")
    try:
        result = ai.chat_json(SYSTEM.format(rules=rules), "Diff:\n```diff\n" + ai.truncate(diff, 18000) + "\n```")
    except Exception as e:  # noqa: BLE001 - AI problems must never block the PR (fail-open)
        ai.log(str(e))
        ai.upsert_comment(pr, MARKER, f"## 🤖 AI Code Review\n\n⚠️ Không gọi được AI: `{e}`\n\nBỏ qua (fail-open).")
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

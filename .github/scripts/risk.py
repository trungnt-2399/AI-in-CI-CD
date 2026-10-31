#!/usr/bin/env python3
"""Deploy risk gate = deterministic rules + AI judgement.

Final level = max(rule level, AI level). Rules give a predictable floor
(dependency / pipeline changes are never "low"), AI adds context.
Outputs: level (low|medium|high), score (0-100).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ai  # noqa: E402

LEVELS = ["low", "medium", "high"]
ZERO_SHA = "0" * 40
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

SYSTEM = """You are a release manager for a Flutter app. Assess the risk of deploying this
change to production. Consider: business logic (prices, payments, auth), dependency changes,
breaking UI flows, missing tests, config/pipeline changes, size of change.
Write reasons in Vietnamese.

Return JSON:
{
  "level": "low|medium|high",
  "score": 0-100,
  "reasons": ["short bullet", "..."],
  "verify_after_deploy": ["what a human/smoke test should check", "..."]
}"""


def level_of(score: int) -> str:
    return "high" if score >= 60 else "medium" if score >= 30 else "low"


def rule_score(files: list[str], lines_changed: int) -> tuple[int, list[str]]:
    score, reasons = 0, []
    if any(f.endswith("pubspec.yaml") for f in files):
        score += 60
        reasons.append("Thay đổi `pubspec.yaml` (dependency/version)")
    if any(f.startswith(".github/") for f in files):
        score += 30
        reasons.append("Thay đổi pipeline `.github/`")
    if any(f.startswith(("android/", "ios/")) for f in files):
        score += 30
        reasons.append("Thay đổi native config (android/ios)")
    lib_changed = any(f.startswith("lib/") for f in files)
    test_changed = any(f.startswith("test/") for f in files)
    if lib_changed and not test_changed:
        score += 15
        reasons.append("Sửa `lib/` nhưng không có test đi kèm")
    if lines_changed > 300:
        score += 30
        reasons.append(f"Thay đổi lớn ({lines_changed} dòng)")
    elif lines_changed > 100:
        score += 15
        reasons.append(f"Thay đổi vừa ({lines_changed} dòng)")
    return min(score, 100), reasons


def main() -> int:
    head = os.getenv("HEAD_SHA", "HEAD")
    base = os.getenv("BEFORE", "")
    if not base or base == ZERO_SHA:
        base = f"{head}~1"
    if ai.sh("git", "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}", check=False).strip():
        commits = ai.sh("git", "log", "--pretty=format:- %h %s", f"{base}..{head}")
    else:  # first push / force-push: compare against the empty tree
        base = EMPTY_TREE
        commits = ai.sh("git", "log", "-n", "20", "--pretty=format:- %h %s", head)

    files = [f for f in ai.sh("git", "diff", "--name-only", base, head).splitlines() if f]
    numstat = ai.sh("git", "diff", "--numstat", base, head).splitlines()
    lines_changed = sum(int(a) + int(d) for a, d, *_ in (l.split("\t") for l in numstat) if a.isdigit() and d.isdigit())
    diff = ai.sh("git", "diff", base, head, "--", ".", ":(exclude)pubspec.lock")

    r_score, r_reasons = rule_score(files, lines_changed)
    try:
        a = ai.chat_json(SYSTEM, f"Commits:\n{commits}\n\nFiles:\n" + "\n".join(files)
                         + "\n\nDiff:\n```diff\n" + ai.truncate(diff, 14000) + "\n```")
        a_level = a.get("level") if a.get("level") in LEVELS else "medium"
        a_score = int(a.get("score", 50))
    except (ai.AIError, ValueError) as e:
        ai.log(f"AI unavailable -> fail-safe 'medium': {e}")
        a = {"reasons": [f"AI không khả dụng ({e}) → mặc định medium"], "verify_after_deploy": []}
        a_level, a_score = "medium", 50

    r_level = level_of(r_score)
    level = max(r_level, a_level, key=LEVELS.index)
    score = max(r_score, a_score)
    icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}[level]

    md = [f"## 🚦 AI Deploy Risk Gate: {icon} **{level.upper()}** ({score}/100)", "",
          f"| | Level | Score |", "|---|---|---|",
          f"| Rules | {r_level} | {r_score} |", f"| AI (`{ai.AI_MODEL}`) | {a_level} | {a_score} |", "",
          "**Lý do (rules):**", *(f"- {x}" for x in r_reasons or ["(không có)"]), "",
          "**Lý do (AI):**", *(f"- {x}" for x in a.get("reasons") or ["(không có)"]), "",
          "**Cần kiểm tra sau deploy:**", *(f"- [ ] {x}" for x in a.get("verify_after_deploy") or ["Smoke test trang chủ"]), ""]
    md.append("⏸️ Risk HIGH → cần người duyệt (environment `production-approval`)." if level == "high"
              else "▶️ Risk chấp nhận được → auto deploy.")
    ai.write_summary("\n".join(md))
    ai.set_output("level", level)
    ai.set_output("score", str(score))
    return 0


if __name__ == "__main__":
    sys.exit(main())

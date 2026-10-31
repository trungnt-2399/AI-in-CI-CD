#!/usr/bin/env python3
"""Generate release notes (dev changelog + short store notes) for a tag."""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ai  # noqa: E402

SYSTEM = """You write release notes for a Flutter mobile/web app.
From the commit list and diff stat, produce Markdown with these sections (omit empty ones):

## ✨ Tính năng mới
## 🐛 Sửa lỗi
## 🔧 Kỹ thuật / nội bộ
## ⚠️ Lưu ý khi nâng cấp

Then a final section:
## 📱 Store release notes
- **VI:** (<= 300 characters, friendly, for end users, no technical words)
- **EN:** (<= 300 characters, same content)

Group related commits, rewrite them in plain language, reference short SHAs or PR numbers.
Do NOT invent changes that are not in the commits. Output Markdown only."""


def main() -> int:
    tag = os.environ["TAG"]
    prev = ai.sh("git", "describe", "--tags", "--abbrev=0", f"{tag}^", check=False).strip()
    rng = f"{prev}..{tag}" if prev else tag
    commits = ai.sh("git", "log", "--pretty=format:- %h %s (%an)", rng)
    stat = ai.sh("git", "diff", "--stat", prev, tag) if prev else ""

    header = f"# {tag}\n\n" + (f"Thay đổi từ `{prev}`.\n\n" if prev else "Bản phát hành đầu tiên.\n\n")
    try:
        notes = ai.chat(SYSTEM, f"Tag: {tag}\nPrevious: {prev or '(none)'}\n\nCommits:\n"
                        + ai.truncate(commits, 10000) + "\n\nDiff stat:\n" + ai.truncate(stat, 4000),
                        max_tokens=1200)
    except ai.AIError as e:
        ai.log(str(e))
        notes = "## Commits\n" + commits  # fallback: plain changelog

    full = header + notes.strip() + ai.footer()
    with open("release_notes.md", "w", encoding="utf-8") as f:
        f.write(full)
    ai.write_summary(full)
    return 0


if __name__ == "__main__":
    sys.exit(main())

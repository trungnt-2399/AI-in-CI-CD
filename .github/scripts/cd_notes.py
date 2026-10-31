#!/usr/bin/env python3
"""Build notes for the mobile CD workflow.

  cd_notes.py --collect   write .cd/commits.txt + .cd/changes.diff (since last build/<env>/* tag)
  cd_notes.py --render    turn Claude's JSON (NOTES_JSON) into build_notes.md + job summary
"""

from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import ai  # noqa: E402

OUT_DIR = ".cd"
ENV = os.getenv("APP_ENV", "staging")
TYPE_LABEL = {"feature": "✨ Mới", "fix": "🐛 Sửa lỗi", "improvement": "⚡ Cải thiện", "internal": "🔧 Nội bộ"}


def last_build_tag() -> str:
    tags = ai.sh("git", "tag", "--list", f"build/{ENV}/*", "--sort=-creatordate", check=False).split()
    return tags[0] if tags else ""


def collect() -> int:
    base = last_build_tag()
    if base:
        commits = ai.sh("git", "log", "--no-merges", "--pretty=format:- %h %s (%an)", f"{base}..HEAD")
        diff = ai.sh("git", "diff", base, "HEAD", "--", ".", ":(exclude)pubspec.lock", ":(exclude).github")
    else:  # first build for this environment
        commits = ai.sh("git", "log", "--no-merges", "-n", "30", "--pretty=format:- %h %s (%an)")
        diff = "(lần build đầu tiên cho môi trường này — không có diff so sánh)"
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(f"{OUT_DIR}/commits.txt", "w", encoding="utf-8") as f:
        f.write(commits or "(không có commit mới)")
    with open(f"{OUT_DIR}/changes.diff", "w", encoding="utf-8") as f:
        f.write(ai.truncate(diff, 60000))
    ai.set_output("base", base)
    return 0


def read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except OSError:
        return ""


def version() -> str:
    m = re.search(r"^version:\s*([^\s+]+)", read("pubspec.yaml"), re.MULTILINE)
    return m.group(1) if m else "?"


def render() -> int:
    build = os.getenv("BUILD_NUMBER", "?")
    base = os.getenv("BASE_REF", "")
    raw = os.getenv("NOTES_JSON", "").strip()
    try:
        d = json.loads(raw) if raw else None
    except json.JSONDecodeError:
        d = None

    lines = [f"# 📱 Build `{ENV}` #{build} — v{version()}", ""]
    lines.append(f"Thay đổi kể từ build trước: `{base}`" if base else "Bản build đầu tiên cho môi trường này.")
    lines.append("")
    if isinstance(d, dict):
        lines += ["## Có gì mới", d.get("summary", ""), ""]
        if d.get("changes"):
            lines += [f"- {TYPE_LABEL.get(c.get('type'), '•')}: {c.get('description', '')}" for c in d["changes"]]
            lines.append("")
        lines += ["## 📋 QA checklist (test trên máy thật)"]
        lines += [f"- [ ] {x}" for x in d.get("qa_checklist") or []]
        if d.get("risks"):
            lines += ["", "## ⚠️ Rủi ro cần để ý", *[f"- {x}" for x in d["risks"]]]
        lines += ["", "---", "<sub>🤖 Claude Code viết từ danh sách commit · AI có thể sai — đối chiếu với ticket.</sub>"]
    else:
        commits = read(f"{OUT_DIR}/commits.txt")
        lines += ["## Commits", commits or "(không có)", "", "<sub>⚠️ AI không khả dụng — hiển thị commit thô.</sub>"]

    md = "\n".join(lines)
    with open("build_notes.md", "w", encoding="utf-8") as f:
        f.write(md + "\n")
    print(md)
    return 0


if __name__ == "__main__":
    if "--collect" in sys.argv:
        sys.exit(collect())
    sys.exit(render())

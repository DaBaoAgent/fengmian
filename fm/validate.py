"""发布信息校验：移植三眼（tuiyan）validate_publication_info.py 的判定规则。

规则：恰好两行；标题 ≤25 字、两段式（：？ ！分隔）、含阿拉伯数字；第二行恰好 4 个 #话题。
"""
from __future__ import annotations

import re
from pathlib import Path

SEPARATOR_RE = re.compile(r"[：:？?！!]")
HASHTAG_RE = re.compile(r"#[^\s#]+")


def check(path: Path) -> dict:
    issues: list[str] = []
    lines = [ln.strip() for ln in path.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
    title = ""
    if len(lines) != 2:
        issues.append(f"必须恰好两行（标题 + 4 个话题），实际 {len(lines)} 行")
    else:
        title = lines[0]
        tags = lines[1].split()
        valid = [t for t in tags if HASHTAG_RE.fullmatch(t)]
        if len(tags) != 4 or len(valid) != 4:
            issues.append(f"第二行必须恰好 4 个 #话题，实际 {len(valid)} 个")
        if len(title) > 25:
            issues.append(f"标题必须≤25 字，实际 {len(title)} 字")
        parts = SEPARATOR_RE.split(title, maxsplit=1)
        if len(parts) != 2 or not parts[0].strip() or not parts[1].strip():
            issues.append("标题必须两段式（问号 / 冒号 / 感叹号分隔）")
        if not re.search(r"[0-9]", title):
            issues.append("标题里的数量请用阿拉伯数字")
    return {"file": path.name, "valid": not issues, "title": title, "issues": issues}

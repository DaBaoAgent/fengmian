"""交付门禁：交付目录根只允许最终交付物，多余封面 / 提示词一律拦住。

规则（固化）：
  根目录允许 = 成片 + 封面-4比3.* + 封面-3比4.* + 发布信息.txt + 任意子目录（源文件等）。
  根目录其余名字里带 封面 / cover / 即梦 / 提示词 的文件 = 多余产物，交付前必须清掉。
"""
from __future__ import annotations

import re
import shutil
from datetime import date
from pathlib import Path

CANONICAL = re.compile(r"封面-4比3\.(png|jpg|jpeg|webp)|封面-3比4\.(png|jpg|jpeg|webp)", re.I)
PUBLISH = re.compile(r"发布信息\.txt", re.I)
VIDEO = re.compile(r"\.(mp4|mov|mkv|avi)$", re.I)
EXTRA = re.compile(r"封面|cover|即梦|提示词", re.I)


def scan(root: Path) -> dict:
    root = root.resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"目录不存在：{root}")

    allowed: list[str] = []
    extras: list[str] = []
    for item in sorted(root.iterdir()):
        if item.is_dir():
            allowed.append(item.name + "/")
            continue
        name = item.name
        if CANONICAL.fullmatch(name) or PUBLISH.fullmatch(name) or VIDEO.search(name):
            allowed.append(name)
        elif EXTRA.search(name):
            extras.append(name)
        else:
            allowed.append(name)  # 与封面无关的文件不归本门禁管

    missing = [n for n in ("封面-4比3", "封面-3比4", "发布信息.txt")
               if not any(a.startswith(n) for a in allowed)]
    return {"root": str(root), "allowed": allowed, "extras": extras, "missing": missing}


def apply(root: Path, archive: bool = True, dry_run: bool = False) -> dict:
    result = scan(root)
    if dry_run or not result["extras"]:
        result["removed"] = []
        return result

    root = Path(result["root"])
    removed: list[str] = []
    bucket = root / "源文件" / f"已删除-{date.today().isoformat()}"
    for name in result["extras"]:
        src = root / name
        if archive:
            bucket.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(bucket / name))
        else:
            src.unlink()
        removed.append(name)
    result["removed"] = removed
    result["archived_to"] = str(bucket) if archive else ""
    return result

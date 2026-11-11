#!/usr/bin/env python
"""把远程生成的封面图落盘并归一到指定像素（tuiyan 规格：4:3=2048x1536，3:4=1536x2048）。

用法：python scripts/save_cover.py --url <图片地址> --out <目标文件> --size 2048x1536
"""
from __future__ import annotations

import argparse
import io
import urllib.request
from pathlib import Path

from PIL import Image


def fetch(url: str) -> Image.Image:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return Image.open(io.BytesIO(resp.read())).convert("RGB")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--size", default="2048x1536", help="宽x高")
    args = p.parse_args()

    w, h = (int(x) for x in args.size.lower().split("x"))
    img = fetch(args.url)
    target = img.resize((w, h), Image.LANCZOS)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    target.save(out, format="PNG")
    print(f"✓ {out}  {img.width}x{img.height} → {w}x{h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

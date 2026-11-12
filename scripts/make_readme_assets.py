#!/usr/bin/env python
"""生成 README 用的示例图（纯代码渲染，不调用生图）：

  1. docs/example-covers.png —— 两张真实封面并排（4:3 / 3:4），带尺寸标注
  2. docs/example-cli.png    —— 真实命令行输出渲染成终端窗口样式

用法：
  python scripts/make_readme_assets.py \
      --covers "…\\001 会飞的中国人" --cli docs/cli-output.txt --out docs
"""
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

MONO = "C:/Windows/Fonts/consola.ttf"
MONO_BOLD = "C:/Windows/Fonts/consolab.ttf"
CJK = "C:/Windows/Fonts/msyh.ttc"


def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def make_covers(covers_dir: Path, out: Path) -> Path:
    left = Image.open(covers_dir / "封面-4比3.png").convert("RGB")
    right = Image.open(covers_dir / "封面-3比4.png").convert("RGB")

    target_h = 760
    left = left.resize((round(left.width * target_h / left.height), target_h), Image.LANCZOS)
    right = right.resize((round(right.width * target_h / right.height), target_h), Image.LANCZOS)

    margin, gap, caption_h = 36, 36, 52
    width = margin * 2 + left.width + gap + right.width
    height = margin * 2 + target_h + caption_h
    canvas = Image.new("RGB", (width, height), "#ffffff")
    canvas.paste(left, (margin, margin))
    canvas.paste(right, (margin + left.width + gap, margin))

    draw = ImageDraw.Draw(canvas)
    f = font(MONO, 24)
    labels = ["4:3   2048 x 1536", "3:4   1536 x 2048"]
    xs = [margin, margin + left.width + gap]
    for label, x in zip(labels, xs):
        draw.text((x, margin + target_h + 14), label, fill="#5a6472", font=f)

    target = out / "example-covers.png"
    canvas.save(target, format="PNG")
    return target


def make_cli(cli_txt: Path, out: Path) -> Path:
    lines = cli_txt.read_text(encoding="utf-8").splitlines()
    f = font(CJK, 24)
    line_h = 34
    pad = 34
    width = max(880, max(len(ln) for ln in lines) * 13 + pad * 2)
    bar_h = 52
    height = bar_h + pad * 2 + line_h * len(lines)
    canvas = Image.new("RGB", (width, height), "#1c1c1c")
    draw = ImageDraw.Draw(canvas)

    draw.rectangle([0, 0, width, bar_h], fill="#2b2b2b")
    for i, color in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        cx = 26 + i * 26
        draw.ellipse([cx, bar_h // 2 - 7, cx + 14, bar_h // 2 + 7], fill=color)
    draw.text((126, bar_h // 2 - 13), "fengmian · 交付门禁", fill="#d8d8d8", font=font(CJK, 20))

    y = bar_h + pad
    for ln in lines:
        color = "#8be9a8" if ln.strip().startswith(("✓", "$")) else "#e6e6e6"
        if '"extras"' in ln or '"removed"' in ln:
            color = "#ffd479"
        draw.text((pad, y), ln, fill=color, font=f)
        y += line_h

    target = out / "example-cli.png"
    canvas.save(target, format="PNG")
    return target


def make_previews(covers_dir: Path, out: Path, long_edge: int = 1800, quality: int = 92) -> list[Path]:
    """把两张真实封面各出一版适合 README 展示的 JPG（不改变构图，只缩边长 + 压质量）。"""
    made: list[Path] = []
    for src_name, dst_name in (("封面-4比3.png", "preview-4x3.jpg"), ("封面-3比4.png", "preview-3x4.jpg")):
        img = Image.open(covers_dir / src_name).convert("RGB")
        scale = long_edge / max(img.width, img.height)
        if scale < 1:
            img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)
        target = out / dst_name
        img.save(target, format="JPEG", quality=quality, optimize=True, progressive=True)
        made.append(target)
    return made


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--covers", required=True, help="含 封面-4比3.png / 封面-3比4.png 的目录")
    p.add_argument("--cli", required=True, help="命令行输出文本")
    p.add_argument("--out", default="docs")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for p in make_previews(Path(args.covers), out):
        print(f"✓ {p}")
    print(f"✓ {make_covers(Path(args.covers), out)}")
    print(f"✓ {make_cli(Path(args.cli), out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

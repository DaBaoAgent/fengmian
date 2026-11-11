#!/usr/bin/env python
"""fengmian —— 一条视频文案 → 两张封面提示词 + 一份发布信息。

来源：Auto-Video · tuiyan 管线发布层（gen_covers_ark.mjs / validate_publication_info.py）。

用法：
  python fengmian.py analyze --src 字幕.srt [--name 片名] [--out 工作目录]
  python fengmian.py build   --src 字幕.srt --out 交付目录 \
        [--name 片名] [--main 六字主标题] [--sub 八字副标题] \
        [--style tuiyan|laolang] [--scene43 横版画面] [--scene34 竖版画面] \
        [--title "前段：后段"] [--tags "#a #b #c #d"]
  python fengmian.py validate --dir 交付目录
  python fengmian.py covers  --dir 交付目录 [--backend ark]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from fm import analyze as A
from fm import cover as C
from fm import gate as G
from fm import publish as P
from fm import validate as V

ROOT = Path(__file__).resolve().parent


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")
    print(f"  ✓ {path}")


def cmd_analyze(args) -> int:
    result = A.analyze(Path(args.src), args.name)
    out_dir = Path(args.out) if args.out else Path(args.src).parent
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / "文案解析.json"
    _write(target, json.dumps(result, ensure_ascii=False, indent=2))
    print(f"建议主标：{result['suggested_main']}  副标：{result['suggested_sub']}")
    print(f"建议话题：{' '.join(result['suggested_tags'])}")
    return 0


def cmd_gate(args) -> int:
    result = G.apply(Path(args.dir), archive=not args.delete, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    ok = not result["missing"] and (args.dry_run or not result["extras"])
    return 0 if ok else 1


def cmd_build(args) -> int:
    src = Path(args.src)
    parsed = A.analyze(src, args.name)
    out_dir = Path(args.out)
    assets = out_dir / "源文件"   # 提示词与元信息归 源文件，交付根只留最终交付物
    assets.mkdir(parents=True, exist_ok=True)

    main = args.main or parsed["suggested_main"]
    sub = args.sub or parsed["suggested_sub"]
    scenes = {
        "4x3": args.scene43 or "画面主体位于中部，左右留出标题呼吸区，环境交代清楚，无人物正脸特写。",
        "3x4": args.scene34 or "主体位于中下部朝画面深处，上部三分之一留作标题净空，环境层次向上延伸。",
    }

    prompts = C.build(main, sub, scenes["4x3"], scenes["3x4"], args.style)
    _write(assets / "封面提示词-4比3.txt", prompts["ratio_4x3"] + "\n")
    _write(assets / "封面提示词-3比4.txt", prompts["ratio_3x4"] + "\n")

    tag_override = args.tags.split() if args.tags else None
    if args.title or tag_override:
        info = P.from_analysis(parsed, title=args.title, tags=tag_override)
    else:
        info = P.from_analysis(parsed)
    _write(out_dir / "发布信息.txt", info)

    meta = {
        "source": str(src),
        "name": parsed["name"],
        "style": args.style,
        "main": main,
        "sub": sub,
        "scene_4x3": scenes["4x3"],
        "scene_3x4": scenes["3x4"],
        "publish_info": info.strip().splitlines(),
        "suggested_tags": parsed["suggested_tags"],
        "hooks": parsed["hooks"][:4],
        "numbers": parsed["numbers"][:6],
    }
    _write(assets / "封面元信息.json", json.dumps(meta, ensure_ascii=False, indent=2))

    check = V.check(out_dir / "发布信息.txt")
    print(json.dumps(check, ensure_ascii=False, indent=2))
    if args.gate:
        gate = G.scan(out_dir)
        if gate["extras"]:
            print("✗ 交付门禁未过：根目录有多余封面/提示词，交付前必须清掉："
                  + "、".join(gate["extras"]))
            return 1
        print("✓ 交付门禁通过：根目录没有多余封面/提示词")
        if gate["missing"]:
            print("  （封面尚未出图：还需 " + "、".join(gate["missing"]) + "）")
    return 0 if check["valid"] else 1


def cmd_validate(args) -> int:
    root = Path(args.dir)
    files = sorted(root.rglob("发布信息.txt"))
    results = [V.check(f) for f in files]
    payload = {
        "root": str(root),
        "file_count": len(results),
        "valid_count": sum(r["valid"] for r in results),
        "invalid_count": sum(not r["valid"] for r in results),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if results and payload["invalid_count"] == 0 else 1


def cmd_covers(args) -> int:
    out_dir = Path(args.dir)
    if args.backend != "ark":
        print("当前后端只支持 ark；未配置密钥时直接使用封面提示词-4比3.txt / -3比4.txt 手动出图。")
        return 0
    meta = json.loads((out_dir / "封面元信息.json").read_text(encoding="utf-8"))
    cmd = [
        "node", str(ROOT / "scripts" / "gen_covers_ark.mjs"),
        "--out", str(out_dir),
        "--prompt43", str(out_dir / "封面提示词-4比3.txt"),
        "--prompt34", str(out_dir / "封面提示词-3比4.txt"),
    ]
    print(" ".join(cmd))
    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(description="视频文案 → 封面提示词 / 发布信息")
    sub = parser.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("analyze", help="解析文案，输出钩子/关键词/数字与建议标题")
    a.add_argument("--src", required=True)
    a.add_argument("--name")
    a.add_argument("--out")
    a.set_defaults(func=cmd_analyze)

    b = sub.add_parser("build", help="生成两张封面提示词 + 发布信息 + 元信息")
    b.add_argument("--src", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--name")
    b.add_argument("--main", help="6 字主标题")
    b.add_argument("--sub", help="8 字副标题")
    b.add_argument("--style", default="tuiyan", help="tuiyan / laolang / 自定义风格描述")
    b.add_argument("--scene43")
    b.add_argument("--scene34")
    b.add_argument("--title", help='两段式发布标题，如 "传说里的中国人：骑车比飞机还快"')
    b.add_argument("--tags", help='4 个话题，空格分隔，如 "#潘德明 #环球旅行 #民国往事 #会飞的中国人"')
    b.add_argument("--gate", action=argparse.BooleanOptionalAction, default=True,
                   help="构建后自检：根目录不得有多余封面/提示词（默认开）")
    b.set_defaults(func=cmd_build)

    g = sub.add_parser("gate", help="交付门禁：清掉根目录多余的封面 / 提示词")
    g.add_argument("--dir", required=True)
    g.add_argument("--dry-run", action="store_true", help="只检查不处理")
    g.add_argument("--delete", action="store_true",
                   help="真删；默认移到 源文件\\已删除-日期 以便回溯")
    g.set_defaults(func=cmd_gate)

    v = sub.add_parser("validate", help="校验目录下所有 发布信息.txt")
    v.add_argument("--dir", default=".")
    v.set_defaults(func=cmd_validate)

    c = sub.add_parser("covers", help="调用方舟 Seedream 出两张封面")
    c.add_argument("--dir", required=True)
    c.add_argument("--backend", default="prompt")
    c.set_defaults(func=cmd_covers)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())

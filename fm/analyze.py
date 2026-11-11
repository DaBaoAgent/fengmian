"""解析视频文案（字幕 srt / 口播稿 txt / 简介 md），抽出可用的钩子、关键词与数字。"""
from __future__ import annotations

import json
import re
from pathlib import Path

SRT_INDEX = re.compile(r"^\d+$")
SRT_TIME = re.compile(r"\d{2}:\d{2}:\d{2}[,.]\d{3}\s*-->")

# 反常识 / 反转 / 悬念标记：命中越多，越适合做封面钩子
HOOK_MARKERS = (
    "却", "竟然", "没想到", "原来", "不是", "反而", "比", "传说", "谜", "遗忘",
    "被忘", "骂", "骗", "第一个", "唯一", "整整", "没想到", "居然", "竟然",
)
DIGIT_RE = re.compile(r"[0-9]+")
CN_NUM_RE = re.compile(r"[一二三四五六七八九十百千万零两]{1,8}(?:年|个|次|天|小时|国|人|岁)")

STOP_CHARS = set("的了是我你他她它们在有和就都而及与着或一个不是也就很还说要来去这那")

# 话题层面的泛词：出现频率高但做不了话题标签
TAG_STOP = {"中国", "上海", "亚洲", "世界", "时候", "地方", "年轻人", "一个人", "我们", "他们", "这个", "那个", "自己", "国家", "历史"}


def load_text(path: Path) -> str:
    """读字幕 / 文案。srt 去掉序号与时间轴，只留正文。"""
    raw = path.read_text(encoding="utf-8-sig", errors="replace")
    if path.suffix.lower() == ".srt":
        lines = []
        for line in raw.splitlines():
            line = line.strip()
            if not line or SRT_INDEX.match(line) or SRT_TIME.search(line):
                continue
            lines.append(line)
        raw = "\n".join(lines)
    return raw


def sentences(text: str) -> list[str]:
    out = []
    for block in re.split(r"[。！？!?；;\n]+", text):
        block = re.sub(r"[，,、：:（）()「」“”\"']", "", block).strip()
        if 6 <= len(block) <= 40:
            out.append(block)
    return out


def numbers(text: str) -> list[str]:
    found = DIGIT_RE.findall(text) + CN_NUM_RE.findall(text)
    seen, out = set(), []
    for item in found:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out[:12]


def keywords(text: str, top: int = 10, for_tags: bool = False) -> list[str]:
    """无分词依赖的关键词：统计 2~4 字连续片段，过滤停用字与虚词组合。"""
    clean = re.sub(r"[^\u4e00-\u9fa5]", "", text)
    counter: dict[str, int] = {}
    for size in (2, 3, 4):
        for i in range(len(clean) - size + 1):
            gram = clean[i:i + size]
            if any(ch in STOP_CHARS for ch in gram):
                continue
            counter[gram] = counter.get(gram, 0) + 1
    ranked = sorted(counter.items(), key=lambda kv: (kv[1] * len(kv[0]), kv[1]), reverse=True)
    picked: list[str] = []
    for gram, count in ranked:
        if count < 2:
            break
        if for_tags and (gram in TAG_STOP or len(gram) < 3):
            continue
        if any(gram in p or p in gram for p in picked):
            continue
        picked.append(gram)
        if len(picked) >= top:
            break
    return picked


def _score(sentence: str) -> float:
    score = 0.0
    for marker in HOOK_MARKERS:
        if marker in sentence:
            score += 1.0
    if DIGIT_RE.search(sentence) or CN_NUM_RE.search(sentence):
        score += 1.2
    score += min(len(sentence), 30) / 60.0
    return score


def hooks(text: str, top: int = 8) -> list[str]:
    ranked = sorted(sentences(text), key=_score, reverse=True)
    return [s for s in ranked if _score(s) > 1.0][:top] or ranked[:top]


def suggest_main(name: str, kw: list[str]) -> str:
    """封面主标题固定 6 字（tuiyan 规则）。片名本身 6 字直接用。"""
    if len(name) == 6:
        return name
    for gram in kw:
        if len(gram) == 6:
            return gram
    joined = "".join(kw)[:6]
    return joined.ljust(6, "　")


def suggest_sub(hs: list[str], num: list[str]) -> str:
    """副标题固定 8 字。优先在含数字的钩子里，取数字附近的 8 字窗口。"""
    for sentence in hs:
        match = CN_NUM_RE.search(sentence) or DIGIT_RE.search(sentence)
        if not match:
            continue
        body = re.sub(r"[^\u4e00-\u9fa5]", "", sentence)
        token = re.sub(r"[^\u4e00-\u9fa5]", "", match.group(0))
        if len(body) < 8 or len(token) > 8:
            continue
        start = max(0, body.find(token) - 3)
        start = min(start, len(body) - 8)
        return body[start:start + 8]
    for sentence in hs:
        body = re.sub(r"[^\u4e00-\u9fa5]", "", sentence)
        if len(body) >= 8:
            return body[:8]
    return ("".join(num) + (hs[0] if hs else "")).replace(" ", "")[:8].ljust(8, "　")


def analyze(path: Path, name: str | None = None) -> dict:
    text = load_text(path)
    story_name = name or path.stem
    kw = keywords(text)
    tag_kw = keywords(text, top=6, for_tags=True)
    hs = hooks(text)
    num = numbers(text)
    return {
        "source": str(path),
        "name": story_name,
        "chars": len(text),
        "sentence_count": len(sentences(text)),
        "keywords": kw,
        "numbers": num,
        "hooks": hs,
        "suggested_main": suggest_main(story_name, kw),
        "suggested_sub": suggest_sub(hs, num),
        "suggested_tags": [f"#{k}" for k in tag_kw[:4]],
    }


if __name__ == "__main__":  # pragma: no cover
    import sys

    print(json.dumps(analyze(Path(sys.argv[1]), sys.argv[2] if len(sys.argv) > 2 else None),
                     ensure_ascii=False, indent=2))

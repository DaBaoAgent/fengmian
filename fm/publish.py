"""发布信息：tuiyan 两行制 —— 标题 ≤25 字、两段式、含量级阿拉伯数字；次行恰好 4 个 #话题。"""
from __future__ import annotations

SEPARATOR = "："
LIMIT = 25
TAG_COUNT = 4


def build(title_lead: str, title_tail: str, tags: list[str]) -> str:
    title = f"{title_lead}{SEPARATOR}{title_tail}"
    if len(title) > LIMIT:
        raise ValueError(f"标题超过 {LIMIT} 字（{len(title)}）：{title}")
    if len(tags) != TAG_COUNT:
        raise ValueError(f"话题必须恰好 {TAG_COUNT} 个，实际 {len(tags)} 个")
    tags = [t if t.startswith("#") else f"#{t}" for t in tags]
    return f"{title}\n{' '.join(tags)}\n"


def from_analysis(analysis: dict, title: str | None = None, tags: list[str] | None = None) -> str:
    """没有人工定稿时，用解析结果凑一版可校验的草稿；title/tags 可逐项覆盖。"""
    tag_list = tags or analysis["suggested_tags"]
    if title:
        parts = title.split(SEPARATOR, 1)
        if len(parts) == 2:
            return build(parts[0], parts[1], tag_list)
        raise ValueError(f"标题必须是两段式（用「：」分隔）：{title}")
    lead = analysis["suggested_main"].strip("　")
    tail = "、".join(analysis["numbers"][:3])
    return build(lead[:12], tail[:12], tag_list)

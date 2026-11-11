"""封面提示词：tuiyan 规则的 6 字主标 + 8 字副标，出 4:3 与 3:4 两版。"""
from __future__ import annotations

# 风格预设。tuiyan 默认写实纪录片；laolang（上美影手绘赛璐璐）等其它管线用各自预设。
PRESETS = {
    "tuiyan": "电影级写实纪录片封面",
    "laolang": "1980 年代上海美术电影制片厂手绘赛璐璐动画电影海报，平涂色块、清晰墨线勾边、纸张颗粒、低饱和青绿赭石配色",
    "auto": "电影感纪实影像封面，真实光影、浅景深",
}

HEAD_4X3 = "{style}，4:3 横版构图。画面："
HEAD_3X4 = "{style}，3:4 竖版构图。画面："


def _text_rule(main: str, sub: str, vertical: bool) -> str:
    where = "画面正上方约三分之一处居中排列两行书法大字" if vertical else "画面上部居中排列两行书法大字"
    return (
        f"{where}，文字醒目、笔画清晰、无变形、无错字："
        f"第一行主标题“{main}”——特大号金黄色粗毛笔书法字，刚劲有力，黑色细描边，柔和黑色投影，几乎横贯版面宽度；"
        f"第二行副标题“{sub}”——中号白色毛笔书法字，与主标题同风格描边和投影，宽度约为主标题三分之二，紧贴主标题下方居中。"
        "文字有安全边距，笔画不裁切。除这两行文字外画面无其他文字、无英文、无 logo、无水印。"
        "背景高清、细节丰富、景深自然，主体突出，构图平衡，色彩高级。"
    )


def build(main: str, sub: str, scene43: str, scene34: str, style: str = "tuiyan") -> dict:
    st = PRESETS.get(style, style)
    if len(main) != 6:
        raise ValueError(f"主标题必须 6 字，实际 {len(main)} 字：{main}")
    if len(sub) != 8:
        raise ValueError(f"副标题必须 8 字，实际 {len(sub)} 字：{sub}")
    return {
        "style": style,
        "ratio_4x3": HEAD_4X3.format(style=st) + scene43 + _text_rule(main, sub, False),
        "ratio_3x4": HEAD_3X4.format(style=st) + scene34 + _text_rule(main, sub, True),
        "main": main,
        "sub": sub,
    }

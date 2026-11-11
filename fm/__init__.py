"""fengmian —— 从视频文案自动产出封面提示词与发布信息的独立模块。

模块来源：Auto-Video · tuiyan 管线的「发布层」
  - 封面规则与提示词模板：tuiyan/scripts/gen_covers_ark.mjs（方舟 doubao-seedream）
  - 发布信息规则与校验：tuiyan/scripts/validate_publication_info.py
"""

__all__ = ["analyze", "cover", "publish", "validate"]

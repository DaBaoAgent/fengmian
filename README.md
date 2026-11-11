# fengmian · 视频文案 → 封面 + 发布信息

从 Auto-Video 的 **tuiyan 管线**里把「发布层」单独拆出来的独立小项目：喂一份视频文案（字幕 srt / 口播稿 txt），直接产出 **两张封面（4:3 / 3:4）+ 一份可校验的发布信息**，并在交付前过一道目录门禁。

## 一、来源与边界

| 克隆自 | 作用 | 本项目的落点 |
|---|---|---|
| `tuiyan/scripts/gen_covers_ark.mjs` | 方舟 Seedream 一次出 4:3 + 3:4 两张封面，6 字金黄主标 + 8 字白副标压两行版头 | `scripts/gen_covers_ark.mjs`（保留 Ark 直连，新增 `--prompt43/--prompt34` 读文件与 `--style` 预设） |
| `tuiyan/scripts/validate_publication_info.py` | 发布信息两行制校验（标题 ≤25 字两段式含阿拉伯数字 + 恰好 4 个话题） | `scripts/validate_publication_info.py`（原样移植）、`fm/validate.py`（库内同规则） |

只搬这两块。tuiyan 里的分镜（`build-storyboard.mjs`）、合音（`concat_narration.py`）、音色试听（`voice_samples.py` / `pitch_analyze.py`）、渲染（`start-film-render.ps1`）等一律不带。

新增的部分（tuiyan 原来没有、本项目要的）：**文案解析**（`fm/analyze.py`）与**交付门禁**（`fm/gate.py`）。

## 二、流程

```
视频文案（.srt / .txt）
      │
      ▼
fm/analyze.py   解析正文 → 钩子句、高频词、数字、建议主标 / 副标 / 话题
      │        （产物：源文件\文案解析.json）
      ▼
fm/cover.py     6 字主标 + 8 字副标 + 场景描述 + 风格预设
      │        → 源文件\封面提示词-4比3.txt / -3比4.txt
      ▼
fm/publish.py   两行制发布信息：标题（两段式、含阿拉伯数字、≤25 字）+ 4 个话题
      │        → 发布信息.txt（交付根）
      ▼
出图            ARK_API_KEY 存在时由 gen_covers_ark.mjs 直出；否则用提示词走本机图像能力
      │        → 封面-4比3.png（2048×1536）/ 封面-3比4.png（1536×2048）
      ▼
fm/gate.py      交付门禁：交付根除「源文件」外不得留多余封面 / 提示词
      │
      ▼
fm/validate.py  发布信息硬校验（不过则非零退出）
```

## 三、命令

```powershell
# 1) 只解析，看能抽出哪些钩子 / 关键词 / 数字
python fengmian.py analyze --src "…\会飞的中国人_字幕.srt" --name 会飞的中国人 --out output\001

# 2) 出提示词（进 源文件\）+ 发布信息（进交付根），构建后自动过门禁
python fengmian.py build --src "…\会飞的中国人_字幕.srt" --out output\001 `
  --name 会飞的中国人 --main 会飞的中国人 --sub 一个人骑车绕地球 `
  --style laolang `
  --scene43 "1930 年代澳大利亚山间土路，黄昏暖金逆光……" `
  --scene34 "米白色双翼小飞机从右上角贴着山脊低飞……" `
  --title "会飞的中国人：90年前骑车跑赢飞机" `
  --tags "#会飞的中国人 #潘德明 #环球旅行 #民国往事"

# 3) 出图（有方舟密钥）
$env:ARK_API_KEY="…"; python fengmian.py covers --dir output\001 --backend ark

# 4) 远端出图后落盘归一尺寸
python scripts/save_cover.py --url <图片地址> --out "…\封面-4比3.png" --size 2048x1536

# 5) 交付前跑门禁与校验
python fengmian.py gate --dir "…\001 会飞的中国人" --dry-run     # 只看
python fengmian.py gate --dir "…\001 会飞的中国人" --delete      # 真删多余项
python fengmian.py validate --dir "…\001 会飞的中国人"
```

## 四、交付门禁（固化规则）

**交付根只放最终交付物，多余封面 / 提示词一律清掉后再交。**

| 允许留在交付根 | 说明 |
|---|---|
| 成片 `*.mp4 / *.mov / *.mkv / *.avi` | 最终视频 |
| `封面-4比3.png`、`封面-3比4.png` | 本管线自己出的两张封面（`jpg/jpeg/webp` 亦可） |
| `发布信息.txt` | 两行制发布信息 |
| 任意子目录（`源文件/` 等） | 提示词、元信息、旧交付、空镜等中间产物全部进这里 |

| 判定为多余（根目录出现即拦） | 例 |
|---|---|
| 名字含 `封面 / cover / 即梦 / 提示词` 且不是上面两张正式封面 | `即梦封面提示词.txt`、`cover_4x3.png`、`cover_3x4.png`、`封面提示词-*.txt`、`封面元信息.json` |

- `python fengmian.py gate --dir <交付目录> --dry-run`：只报不改，退出码非零表示未过。
- 默认把多余项移到 `源文件\已删除-<日期>\` 以便回溯；加 `--delete` 直接删。
- `build` 默认带门禁自检（`--no-gate` 可关），构建目录里出现多余封面/提示词会直接非零退出。
- 待补封面时门禁只提示缺 `封面-4比3 / 封面-3比4`，不算失败。

## 五、必须守住的规格（tuiyan 原规则，已固化进代码）

**封面**
- 尺寸：4:3 = `2048×1536`（`封面-4比3.png`）、3:4 = `1536×2048`（`封面-3比4.png`）。
- 版头：**6 字金黄色粗毛笔主标题**（几乎横贯版面）+ **8 字白色毛笔副标题**（宽度约主标 2/3），黑色细描边、柔和黑投影；4:3 版在上部居中，3:4 版在顶部约 1/3 处居中。
- 硬约束：除这两行文字外画面无其他文字、无英文、无 logo、无水印；文字留安全边距、笔画不裁切。
- 字数写错时：`fm/cover.py` 抛错中断，`gen_covers_ark.mjs` 只 `console.warn`（沿用原脚本行为）。
- 图内文字用中文双引号 `“”` 界定，字体、颜色、排版说明写在引号外。

**发布信息**
- 恰好两行，空行不计。
- 第一行标题：≤25 字（含标点）、两段式（`：` `:` `？` `?` `！` `!` 之一分隔，两段都非空）、含量级阿拉伯数字。
- 第二行：恰好 4 个 `#话题`，空格分隔。

## 六、风格预设

`fm/cover.py` 与 `gen_covers_ark.mjs` 共用，`--style` 也可直接传风格字符串覆盖：

| 名称 | 版头前缀 |
|---|---|
| `tuiyan` | 电影级写实纪录片封面（默认） |
| `laolang` | 1980 年代上海美术电影制片厂手绘赛璐璐动画电影海报（平涂色块、墨线勾边、纸张颗粒、低饱和青绿赭石） |
| `auto` | 电影感纪实影像封面 |

## 七、产物清单

`build` 一次写出：
- 交付根：`发布信息.txt`
- `源文件\封面提示词-4比3.txt`、`源文件\封面提示词-3比4.txt`
- `源文件\封面元信息.json`（主标/副标/风格/场景/话题/钩子来源，便于回查版本）

`analyze` 写出 `源文件\文案解析.json`；出图后交付根得两张 `封面-*.png`。

## 八、首例记录（001 会飞的中国人，2026-11-11）

- 输入：`Auto-Video\laolang\out\001 会飞的中国人\源文件\会飞的中国人_字幕.srt`（3,641 字）
- 主标「会飞的中国人」/ 副标「一个人骑车绕地球」，风格 `laolang`
- 封面：`封面-4比3.png`（2048×1536）、`封面-3比4.png`（1536×2048）
- 发布信息：`会飞的中国人：90年前骑车跑赢飞机` + `#会飞的中国人 #潘德明 #环球旅行 #民国往事`（校验通过）
- 交付门禁：删掉 `即梦封面提示词.txt`、`cover_4x3.png`、`cover_3x4.png`，原件备份在 `源文件\旧交付-2026-11-11\`
- 本机无 `ARK_API_KEY`，出图走本机图像能力，提示词与 tuiyan 模板逐字一致

## 九、依赖

Python 3.10+、`Pillow`（`save_cover.py` 归一尺寸用）；`node` 18+（走 Ark 出图时）。Ark 出图需环境变量 `ARK_API_KEY`，模型可用 `ARK_MODEL` 覆盖（默认 `doubao-seedream-4-0-250828`）。

## 十、目录

```
fengmian/
├─ fengmian.py                 # CLI：analyze / build / validate / gate / covers
├─ fm/
│  ├─ analyze.py               # 文案解析：钩子、关键词、数字、建议标题
│  ├─ cover.py                 # 6+8 字版头与提示词、风格预设
│  ├─ publish.py               # 两行制发布信息
│  ├─ validate.py              # 发布信息校验（库内）
│  └─ gate.py                  # 交付门禁：根目录多余封面/提示词拦截
├─ scripts/
│  ├─ gen_covers_ark.mjs        # 方舟 Seedream 出图（移植自 tuiyan）
│  ├─ validate_publication_info.py  # 原样移植自 tuiyan
│  └─ save_cover.py            # 远端图落盘 + 尺寸归一
├─ output/                     # 示例产物（001 会飞的中国人）
└─ README.md
```

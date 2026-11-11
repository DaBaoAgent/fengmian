#!/usr/bin/env node
// 方舟 (Ark) 文生图封面 —— 移植自 Auto-Video · tuiyan/scripts/gen_covers_ark.mjs。
// 规则：6 字金黄色粗毛笔主标题 + 8 字白色毛笔副标题，画面上部两行；除两行文字外无其他文字。
// 用法：
//   ARK_API_KEY=<key> node scripts/gen_covers_ark.mjs --out <目录> \
//     --prompt43 <4:3提示词文件> --prompt34 <3:4提示词文件>
//   或按 tuiyan 原式传参：
//   ARK_API_KEY=<key> node scripts/gen_covers_ark.mjs --out <目录> \
//     --main 六字主标 --sub 八字副标 --scene43 <横版画面> --scene34 <竖版画面> [--style <风格>]
import fs from "node:fs";
import path from "node:path";

const API = "https://ark.cn-beijing.volces.com/api/v3/images/generations";
const MODEL = process.env.ARK_MODEL || "doubao-seedream-4-0-250828";

const PRESETS = {
  tuiyan: "电影级写实纪录片封面",
  laolang: "1980 年代上海美术电影制片厂手绘赛璐璐动画电影海报，平涂色块、清晰墨线勾边、纸张颗粒、低饱和青绿赭石配色",
  auto: "电影感纪实影像封面，真实光影、浅景深",
};

function arg(name, def) {
  const i = process.argv.indexOf("--" + name);
  return i >= 0 ? process.argv[i + 1] : def;
}

const TEXT = (m, s, vertical) =>
  (vertical ? "画面正上方约三分之一处居中排列两行书法大字" : "画面上部居中排列两行书法大字") +
  "，文字醒目、笔画清晰、无变形无错字：" +
  `第一行主标题“${m}”——特大号金黄色粗毛笔书法字，刚劲有力，黑色细描边，柔和黑色投影，几乎横贯版面宽度；` +
  `第二行副标题“${s}”——中号白色毛笔书法字，与主标题同风格描边和投影，宽度约为主标题三分之二，紧贴主标题下方居中。` +
  "文字有安全边距，笔画不裁切。除这两行文字外画面无其他文字、无英文、无logo、无水印。" +
  "背景高清、细节丰富、景深自然，主体突出，构图平衡，色彩高级。";

async function gen(prompt, size, key) {
  const r = await fetch(API, {
    method: "POST",
    headers: { Authorization: "Bearer " + key, "Content-Type": "application/json" },
    body: JSON.stringify({ model: MODEL, prompt, size, response_format: "url", watermark: false }),
  });
  const j = await r.json();
  if (!r.ok || !j.data?.[0]?.url) throw new Error("Ark 返回异常: " + JSON.stringify(j).slice(0, 400));
  return j.data[0].url;
}

async function download(url, dest) {
  const r = await fetch(url);
  if (!r.ok) throw new Error("下载失败 " + r.status);
  const ct = r.headers.get("content-type") || "";
  const ext = ct.includes("png") ? ".png" : ct.includes("webp") ? ".webp" : ".jpg";
  const buf = Buffer.from(await r.arrayBuffer());
  const final = dest + ext;
  fs.writeFileSync(final, buf);
  return { final, bytes: buf.length };
}

async function main() {
  const key = process.env.ARK_API_KEY;
  if (!key) throw new Error("缺少 ARK_API_KEY 环境变量");
  const out = arg("out");
  if (!out) throw new Error("缺少 --out");

  let p43 = arg("prompt43");
  let p34 = arg("prompt34");
  if (p43 && p34) {
    p43 = fs.readFileSync(p43, "utf8").trim();
    p34 = fs.readFileSync(p34, "utf8").trim();
  } else {
    const m = arg("main");
    const s = arg("sub");
    const style = PRESETS[arg("style", "tuiyan")] || arg("style", "tuiyan");
    const s43 = arg("scene43");
    const s34 = arg("scene34");
    if (!m || !s || !s43 || !s34) throw new Error("需要 --prompt43/--prompt34 或 --main/--sub/--scene43/--scene34");
    if (m.length !== 6) console.warn("⚠ 主标题应为 6 字，实际 " + m.length);
    if (s.length !== 8) console.warn("⚠ 副标题应为 8 字，实际 " + s.length);
    p43 = `${style}，4:3 横版构图。画面：${s43}${TEXT(m, s, false)}`;
    p34 = `${style}，3:4 竖版构图。画面：${s34}${TEXT(m, s, true)}`;
  }

  fs.mkdirSync(out, { recursive: true });
  console.log("生成 4:3 (2048x1536) ...");
  const u43 = await gen(p43, "2048x1536", key);
  const f43 = await download(u43, path.join(out, "封面-4比3"));
  console.log("  ✓", f43.final, Math.round(f43.bytes / 1024) + " KB");

  console.log("生成 3:4 (1536x2048) ...");
  const u34 = await gen(p34, "1536x2048", key);
  const f34 = await download(u34, path.join(out, "封面-3比4"));
  console.log("  ✓", f34.final, Math.round(f34.bytes / 1024) + " KB");
  console.log("DONE");
}

main().catch((e) => {
  console.error("失败:", e.message);
  process.exit(1);
});

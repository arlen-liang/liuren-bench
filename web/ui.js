// ui.js：网页版里与页面无关的纯函数——课盘成文、拼提示词、解析 AI 回答、生成预填 issue 链接。
// 与 DOM 无关，node 可测（web/test/ui.test.mjs）。

import { GENERAL_NAMES, KIN_NAMES, ZHI } from "./liuren.js";

export const SHEN_NAMES = { 子: "神后", 丑: "大吉", 寅: "功曹", 卯: "太冲", 辰: "天罡", 巳: "太乙",
  午: "胜光", 未: "小吉", 申: "传送", 酉: "从魁", 戌: "河魁", 亥: "登明" };

export const PROMPT_VERSION = "liuren-prompt 0.2";
export const REPO = "arlen-liang/liuren-bench";
export const CATEGORIES = ["求职", "工作", "财运", "感情", "健康（仅限本人）", "出行", "失物", "考试", "其他"];

const g = (x) => GENERAL_NAMES[x];

export function chartText(c) {
  const t = c.time;
  const order = [...ZHI].map((z) => [c.plate[z], z, c.generals[z]]);   // [天盘, 地盘, 将]
  const rows = [];
  for (let i = 0; i < 12; i += 4) {
    rows.push("  " + order.slice(i, i + 4).map(([u, d, j]) => `${u}→${d} ${g(j)}`).join("　"));
  }
  const L = c.lessons;
  const names = ["一课", "二课", "三课", "四课"];
  const T = c.transmissions;
  const tn = ["初传", "中传", "末传"];
  return [
    `起课时间：${t.local.slice(0, 16)}（北京时间）`,
    `四柱：${t.year}年 ${t.month}月 ${t.day}日 ${t.hour}时；月将${t.month_general}（${t.solar_term.name}后）`,
    `流派：以《六壬大全》为准，贵人用"甲戊庚牛羊"版；${c.noble.period}占，贵人${c.noble.direction}布`,
    "天盘所临与所乘天将（天盘支→临地盘支，乘将）：",
    ...rows,
    "四课：" + L.map((k, i) => `${names[i]} ${k.up}加${k.down}（${g(k.general)}）`).join("　"),
    `课体：${c.method.gate}·${c.method.name}`,
    "三传：" + T.map((n, i) => `${tn[i]} ${n.branch}（${g(n.general)}，${KIN_NAMES[n.kin]}${n.void ? "，旬空" : ""}）`).join("　"),
    `旬空：${c.void.join("、")}`,
  ].join("\n");
}

const gateKey = (c) => (c.method.gate === "贼克" ? `贼克·${c.method.name}` : c.method.gate);
const uniq = (xs) => [...new Set(xs)];

// 按课盘摘《六壬大全》原文：本课课体、三传所见十二神、三传所乘天将。与 skill/liuren_skill.py 逐字一致
export function excerpts(chart, daquan) {
  const parts = [`【参考原文】以下摘自${daquan.source}，供断课引据，未必句句切题：`];
  parts.push(`〈课体·${gateKey(chart)}〉\n${daquan.gate[gateKey(chart)]}`);
  for (const b of uniq(chart.transmissions.map((n) => n.branch))) parts.push(`〈十二神·${b}（${SHEN_NAMES[b]}）〉\n${daquan.shen[b]}`);
  for (const j of uniq(chart.transmissions.map((n) => n.general))) parts.push(`〈天将·${g(j)}〉\n${daquan.jiang[j]}`);
  return parts.join("\n\n");
}

// 一次替换全部占位符，只扫模板：用户文本里就算写了 {{chart}} 或 $1，也不会被二次替换
export function buildPrompt(template, chart, question, deadline, daquan) {
  const values = { question, deadline, chart: chartText(chart), excerpts: excerpts(chart, daquan) };
  return template.replace(/\{\{(\w+)\}\}/g, (_, k) => values[k]);
}

// 解析 AI 回答里的 liuren-verdict 代码块。只认本项目这几个键，其余忽略。
export function parseVerdict(text) {
  const m = /```liuren-verdict[ \t]*\n([\s\S]*?)```/.exec(text || "");
  if (!m) return null;
  const v = { judge: {} };
  let inJudge = false;
  for (const raw of m[1].split("\n")) {
    const line = raw.replace(/\s+#.*$/, "");
    const kv = /^(\s*)([a-z_]+):\s*(.*?)\s*$/.exec(line);
    if (!kv) continue;
    const [, indent, key, val] = kv;
    const value = val.replace(/^["']|["']$/g, "");
    if (!indent && key === "judge") { inJudge = true; continue; }
    if (indent && inJudge) { v.judge[key] = value; continue; }
    inJudge = false;
    v[key] = value;
  }
  if (v.judge.tools !== undefined) v.judge.tools = /^(true|是|能)/.test(v.judge.tools);
  return v;
}

// 生成预填好的 issue 链接。字段名与 .github/ISSUE_TEMPLATE/live.yml 的 id 一致；
// 确认勾选项不预填，留给提交的人自己勾。
export function issueUrl({ time, question, category, deadline, verdict }) {
  const p = new URLSearchParams({
    template: "live.yml",
    title: `[实占] ${question}`.slice(0, 120),
    time, question, category, deadline,
  });
  if (verdict) {
    const j = verdict.judge || {};
    p.set("judge_type", "AI");
    p.set("model", j.model || "");
    p.set("harness", j.harness || "");
    p.set("skill", j.skill || PROMPT_VERSION);
    p.set("tools", j.tools ? "能（可跑代码或查资料）" : "不能");
    p.set("outcome", verdict.outcome || "");
    if (verdict.outcome === "成" && verdict.window) p.set("window", verdict.window);
    if (verdict.confidence) p.set("confidence", Number(verdict.confidence).toFixed(1));
    p.set("basis", (verdict.basis || "").slice(0, 1500));
  }
  return `https://github.com/${REPO}/issues/new?${p.toString()}`;
}

// 追加到已有 issue 用的回复：带完整代码块标记，粘进 issue 回复框即可
export function verdictBlock(verdict) {
  const j = verdict.judge || {};
  const lines = ["```liuren-verdict", "judge:", `  model: ${j.model}`, `  harness: ${j.harness}`,
    `  skill: ${j.skill || PROMPT_VERSION}`, `  tools: ${j.tools ? "true" : "false"}`, `outcome: ${verdict.outcome}`];
  if (verdict.outcome === "成" && verdict.window) lines.push(`window: ${verdict.window}`);
  lines.push(`confidence: ${Number(verdict.confidence).toFixed(1)}`);
  if (verdict.basis) lines.push(`basis: ${JSON.stringify(verdict.basis.replace(/\s+/g, " "))}`);
  lines.push("```");
  return lines.join("\n");
}

// 当前北京时间，"2026-10-08 14:20"
export function nowBJT(now = Date.now()) {
  const d = new Date(now + 8 * 3600 * 1000);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}`;
}

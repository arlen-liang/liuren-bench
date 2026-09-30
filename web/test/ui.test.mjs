// node --test web/test/
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";
import { castAt, jieqiTable, parseBJT } from "../liuren.js";
import { PROMPT_VERSION, buildPrompt, chartText, issueUrl, nowBJT, parseVerdict } from "../ui.js";

const here = dirname(fileURLToPath(import.meta.url));
const read = (p) => readFileSync(join(here, p), "utf8");
const data = { lessons: JSON.parse(read("../data/lessons.json")), jieqi: jieqiTable(JSON.parse(read("../data/jieqi.json"))) };
const TEMPLATE = read("../../skill/prompt.md");
const DAQUAN = JSON.parse(read("../../skill/duanfa/daquan.json"));

// issue #2 用的课盘文字（手工给出、已交给第二位断者），网页必须逐字一致
const ISSUE2 = `起课时间：2026-09-30 22:52（北京时间）
四柱：丙午年 丁酉月 丁未日 亥时；月将辰（秋分后）
流派：以《六壬大全》为准，贵人用"甲戊庚牛羊"版；夜占，贵人顺布
天盘所临与所乘天将（天盘支→临地盘支，乘将）：
  巳→子 太常　午→丑 玄武　未→寅 太阴　申→卯 天后
  酉→辰 贵人　戌→巳 螣蛇　亥→午 朱雀　子→未 六合
  丑→申 勾陈　寅→酉 青龙　卯→戌 天空　辰→亥 白虎
四课：一课 子加丁（六合）　二课 巳加子（太常）　三课 子加未（六合）　四课 巳加子（太常）
课体：比用·知一
三传：初传 巳（太常，兄弟）　中传 戌（螣蛇，子孙）　末传 卯（天空，父母，旬空）
旬空：寅、卯`;

test("chartText 与 issue #2 的课盘文字逐字一致", () => {
  assert.equal(chartText(castAt(parseBJT("2026-09-30 22:52"), data)), ISSUE2);
});

test("提示词填入问题、截止日、课盘与原文摘录", () => {
  const p = buildPrompt(TEMPLATE, castAt(parseBJT("2026-09-30 22:52"), data), "能否一次通过", "2027-05-31", DAQUAN);
  assert.ok(p.includes("能否一次通过") && p.includes("截止日：2027-05-31") && p.includes("课体：比用·知一"));
  assert.ok(!p.includes("{{"));
  assert.ok(p.includes("skill: liuren-prompt 0.2"));
  assert.ok(p.includes("〈课体·比用〉") && p.includes("〈十二神·巳（太乙）〉") && p.includes("〈天将·太常〉"));
  assert.ok(p.includes("铸印在巳"));                         // 太常条原文
  assert.ok(p.includes("CC BY-SA 4.0"));                    // 注明原文授权
});

test("解析 AI 回答里的断语块", () => {
  const reply = `一番分析……

\`\`\`liuren-verdict
judge:
  model: doubao-1.8   # 自报
  harness: 网页聊天
  skill: liuren-prompt 0.1
  tools: false
outcome: 成
window: 2027-05-01 ~ 2027-05-31
confidence: 0.65
basis: 铸印乘轩，功名之课
\`\`\`
后话`;
  const v = parseVerdict(reply);
  assert.deepEqual(v.judge, { model: "doubao-1.8", harness: "网页聊天", skill: "liuren-prompt 0.1", tools: false });
  assert.equal(v.outcome, "成");
  assert.equal(v.window, "2027-05-01 ~ 2027-05-31");
  assert.equal(v.confidence, "0.65");
  assert.equal(parseVerdict("没有代码块"), null);
});

test("预填 issue 链接", () => {
  const url = new URL(issueUrl({
    time: "2026-09-30 22:52", question: "能否一次通过", category: "考试", deadline: "2027-05-31",
    verdict: { judge: { model: "m", harness: "豆包网页", tools: true }, outcome: "不成", window: "2027-05-01 ~ 2027-05-31", confidence: "0.6", basis: "b" },
  }));
  const q = url.searchParams;
  assert.equal(url.pathname, "/arlen-liang/liuren-bench/issues/new");
  assert.equal(q.get("template"), "live.yml");
  assert.equal(q.get("time"), "2026-09-30 22:52");
  assert.equal(q.get("tools"), "能（可跑代码或查资料）");
  assert.equal(q.get("skill"), PROMPT_VERSION);
  assert.equal(q.get("window"), null);                     // 断不成时不带应期
  assert.equal(q.get("confidence"), "0.6");
  assert.equal(q.get("judge_type"), "AI");
});

test("下拉项的值必须与 issue 表单完全一致", () => {
  const form = read("../../.github/ISSUE_TEMPLATE/live.yml");
  for (const v of ["能（可跑代码或查资料）", "不能", "AI", "成", "不成", "0.5", "1.0", "考试", "健康（仅限本人）"]) {
    assert.ok(form.includes(v), v);
  }
});

test("北京时间", () => {
  assert.equal(nowBJT(Date.UTC(2026, 8, 30, 14, 52)), "2026-09-30 22:52");
});

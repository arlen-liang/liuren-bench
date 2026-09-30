// 用一个极简的假 DOM 跑真实的 app.js，把三步走一遍：起课 → 粘回答 → 生成链接。
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { test } from "node:test";
import { fileURLToPath } from "node:url";

const here = dirname(fileURLToPath(import.meta.url));
const html = readFileSync(join(here, "../index.html"), "utf8");

class El {
  constructor(id) { Object.assign(this, { id, value: "", textContent: "", innerHTML: "", className: "", hidden: false, checked: false, children: [] }); }
  select() {}
  scrollIntoView() {}
  appendChild(c) { this.children.push(c); }
}
const els = {};
for (const [, id] of html.matchAll(/id="([^"]+)"/g)) els[id] = new El(id);
for (const id of ["s2", "s3", "after"]) els[id].hidden = true;

globalThis.document = { getElementById: (id) => els[id] ?? assert.fail(`页面里没有 #${id}`), createElement: () => new El("a") };
Object.defineProperty(globalThis, "navigator", { value: { clipboard: { writeText: async () => {} } }, configurable: true });
globalThis.fetch = async (url) => {
  const p = url.startsWith("../") ? join(here, "../..", url.slice(3)) : join(here, "..", url);
  const text = readFileSync(p, "utf8");
  return { json: async () => JSON.parse(text), text: async () => text };
};

test("三步走通", async () => {
  await import("../app.js");
  await new Promise((r) => setTimeout(r, 50));                 // 等数据加载完
  assert.match(els.time.value, /^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/);
  assert.ok(els.category.innerHTML.includes("考试"));

  els.question.value = "测试能否成";
  els.deadline.value = "2099-12-31";
  els.cast.onclick();
  assert.equal(els.m1.textContent, "");
  assert.equal(els.s2.hidden, false);
  assert.ok(els.chart.textContent.startsWith("起课时间："));
  assert.ok(els.prompt.value.includes("测试能否成") && !els.prompt.value.includes("{{"));

  els.reply.value = "分析……\n```liuren-verdict\njudge:\n  model: 不确定\n  tools: true\noutcome: 成\nwindow: 2099-01-01 ~ 2099-02-01\nconfidence: 0.73\nbasis: 某某\n```";
  els.reply.oninput();
  assert.equal(els.s3.hidden, false);
  assert.equal(els.model.value, "");                          // "不确定"不预填，逼人核对
  assert.equal(els.confidence.value, "0.7");
  assert.equal(els.tools.checked, true);

  els.link.onclick();
  assert.match(els.m3.textContent, /模型和在哪儿用的都要填/);

  els.model.value = "kimi-k2";
  els.harness.value = "Kimi 网页";
  els.link.onclick();
  const a = els.m3.children.at(-1);
  const q = new URL(a.href).searchParams;
  assert.equal(q.get("question"), "测试能否成");
  assert.equal(q.get("model"), "kimi-k2");
  assert.equal(q.get("harness"), "Kimi 网页");
  assert.equal(q.get("window"), "2099-01-01 ~ 2099-02-01");
  assert.equal(els.after.hidden, false);

  els.asreply.onclick();
  await new Promise((r) => setTimeout(r, 10));
  assert.ok(els.replytext.value.startsWith("```liuren-verdict") && els.replytext.hidden === false);
});

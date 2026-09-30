// app.js：网页版的页面逻辑。规则与文字处理都在 liuren.js / ui.js，这里只管 DOM。
import { castAt, jieqiTable, parseBJT } from "./liuren.js";
import { CATEGORIES, PROMPT_VERSION, buildPrompt, chartText, issueUrl, nowBJT, parseVerdict } from "./ui.js";

const $ = (id) => document.getElementById(id);
const msg = (id, text, kind = "err") => { const el = $(id); el.textContent = text; el.className = `msg ${text ? kind : ""}`; };

let data = null, template = "", daquan = null, current = null;

async function load() {
  const [lessons, jieqi, tpl, dq] = await Promise.all([
    fetch("data/lessons.json").then((r) => r.json()),
    fetch("data/jieqi.json").then((r) => r.json()),
    fetch("../skill/prompt.md").then((r) => r.text()),
    fetch("../skill/duanfa/daquan.json").then((r) => r.json()),
  ]);
  data = { lessons, jieqi: jieqiTable(jieqi) };
  template = tpl;
  daquan = dq;
}

function init() {
  $("category").innerHTML = CATEGORIES.map((c) => `<option>${c}</option>`).join("");
  $("time").value = nowBJT();
  $("pv").textContent = PROMPT_VERSION;
  $("now").onclick = () => { $("time").value = nowBJT(); };

  $("cast").onclick = () => {
    msg("m1", "");
    const time = $("time").value.trim(), question = $("question").value.trim(), deadline = $("deadline").value;
    if (!question) return msg("m1", "占事还没填");
    if (!deadline) return msg("m1", "截止日还没填");
    let utc;
    try { utc = parseBJT(time); } catch (e) { return msg("m1", e.message); }
    const age = (Date.now() - utc) / 3600e3;
    if (age > 24) msg("m1", "起课时间早于现在 24 小时以上，提交后会被机器人标出来");
    if (age < -0.2) return msg("m1", "起课时间在未来");
    if (deadline < time.slice(0, 10)) return msg("m1", "截止日早于起课时间");
    try { current = castAt(utc, data); } catch (e) { return msg("m1", e.message); }
    current.q = { time: time.slice(0, 16), question, category: $("category").value, deadline };
    $("chart").textContent = chartText(current);
    $("prompt").value = buildPrompt(template, current, question, deadline, daquan);
    $("s2").hidden = false;
    $("s2").scrollIntoView({ behavior: "smooth" });
  };

  $("copy").onclick = async () => {
    try { await navigator.clipboard.writeText($("prompt").value); msg("m2", "已复制", "ok"); }
    catch { $("prompt").select(); msg("m2", "浏览器不让自动复制，已选中，请手动复制"); }
  };

  $("reply").oninput = () => {
    const v = parseVerdict($("reply").value);
    if (!v) { $("s3").hidden = true; return msg("m2", "还没找到 ```liuren-verdict 代码块"); }
    msg("m2", "读到断语了，往下核对", "ok");
    $("model").value = v.judge.model && v.judge.model !== "不确定" ? v.judge.model : "";
    $("harness").value = "";
    $("tools").checked = !!v.judge.tools;
    if (["成", "不成"].includes(v.outcome)) $("outcome").value = v.outcome;
    const c = Number(v.confidence);
    if (c >= 0.5 && c <= 1) $("confidence").value = (Math.round(c * 10) / 10).toFixed(1);
    $("window").value = v.window || "";
    $("basis").value = v.basis || "";
    $("s3").hidden = false;
  };

  $("link").onclick = () => {
    msg("m3", "");
    const model = $("model").value.trim(), harness = $("harness").value.trim();
    if (!model || !harness) return msg("m3", "模型和在哪儿用的都要填，缺了这条断语进不了账");
    const outcome = $("outcome").value, win = $("window").value.trim();
    if (outcome === "成" && win && !/^\d{4}-\d{2}-\d{2}\s*~\s*\d{4}-\d{2}-\d{2}$/.test(win)) {
      return msg("m3", "应期格式应为 2027-05-01 ~ 2027-05-31");
    }
    const url = issueUrl({
      ...current.q,
      verdict: { judge: { model, harness, skill: PROMPT_VERSION, tools: $("tools").checked },
                 outcome, window: win, confidence: $("confidence").value, basis: $("basis").value.trim() },
    });
    $("m3").innerHTML = "";
    const a = document.createElement("a");
    a.href = url; a.target = "_blank"; a.rel = "noopener"; a.className = "btn"; a.textContent = "去 GitHub 提交";
    $("m3").appendChild(a);
    $("after").hidden = false;
  };
}

load().then(init).catch((e) => msg("m1", `数据没加载出来：${e.message}`));

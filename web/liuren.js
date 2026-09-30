// liuren.js：网页版起课。浏览器与 node 通用，无依赖。
//
// 时间层与天地盘、四课、天将、六亲、旬空在这里按 core/liuren_core 的规则实现；
// 九宗门的课体与三传查 data/lessons.json（由 Python 引擎导出），不在 JS 里重写。
// CI 用 1000 个随机时刻逐字段比对本文件与 Python 引擎的输出（web/test/compare.mjs）。

export const GAN = "甲乙丙丁戊己庚辛壬癸";
export const ZHI = "子丑寅卯辰巳午未申酉戌亥";
export const JIAZI = Array.from({ length: 60 }, (_, i) => GAN[i % 10] + ZHI[i % 12]);
export const GENERALS = "贵蛇雀合勾龙空虎常玄阴后";
export const GENERAL_NAMES = {
  贵: "贵人", 蛇: "螣蛇", 雀: "朱雀", 合: "六合", 勾: "勾陈", 龙: "青龙",
  空: "天空", 虎: "白虎", 常: "太常", 玄: "玄武", 阴: "太阴", 后: "天后",
};
export const KIN_NAMES = { 父: "父母", 兄: "兄弟", 子: "子孙", 财: "妻财", 官: "官鬼" };

const WUXING = {};
for (const [chars, e] of [["甲乙寅卯", "木"], ["丙丁巳午", "火"], ["戊己辰戌丑未", "土"], ["庚辛申酉", "金"], ["壬癸亥子", "水"]]) {
  for (const c of chars) WUXING[c] = e;
}
const KE = { 木: "土", 土: "水", 水: "火", 火: "金", 金: "木" };
const SHENG = { 木: "火", 火: "土", 土: "金", 金: "水", 水: "木" };
const JIGONG = Object.fromEntries([...GAN].map((g, i) => [g, "寅辰巳未巳未申戌亥丑"[i]]));

// 贵人口诀：[昼贵, 夜贵]
const GUIREN = {
  甲羊: { 甲: "未丑", 乙: "申子", 丙: "酉亥", 丁: "亥酉", 戊: "丑未", 己: "子申", 庚: "丑未", 辛: "寅午", 壬: "卯巳", 癸: "巳卯" },
  甲牛: { 甲: "丑未", 乙: "子申", 丙: "亥酉", 丁: "亥酉", 戊: "丑未", 己: "子申", 庚: "丑未", 辛: "午寅", 壬: "巳卯", 癸: "巳卯" },
};
const DAY_HOURS = "卯辰巳午未申";
const SHUN_SEATS = "亥子丑寅卯辰";

export const DEFAULT_SCHOOL = {
  guiren: "甲牛", daynight: "卯酉", shehai: "count", shehai_count_gan: true, zishi: "子初", true_solar: false,
};

const zi = (z) => ZHI.indexOf(z);
const mod = (a, n) => ((a % n) + n) % n;
const shift = (z, n) => ZHI[mod(zi(z) + n, 12)];
const isYang = (c) => (GAN.includes(c) ? GAN.indexOf(c) : ZHI.indexOf(c)) % 2 === 0;
const ke = (a, b) => KE[WUXING[a]] === WUXING[b];
const sheng = (a, b) => SHENG[WUXING[a]] === WUXING[b];

function liuqin(g, z) {
  if (WUXING[g] === WUXING[z]) return "兄";
  if (sheng(g, z)) return "子";
  if (sheng(z, g)) return "父";
  if (ke(g, z)) return "财";
  return "官";
}

function xunkong(day) {
  const i = JIAZI.indexOf(day);
  const start = zi(JIAZI[i - (i % 10)][1]);
  return [ZHI[(start + 10) % 12], ZHI[(start + 11) % 12]];
}

// ---- 起课：日干支 + 月将 + 占时 ----

export function cast(day, monthGeneral, hour, lessonsTable, school = DEFAULT_SCHOOL) {
  if (!JIAZI.includes(day)) throw new Error(`不是六十甲子：${day}`);
  if (school.shehai !== "count" || school.shehai_count_gan !== true) {
    throw new Error("网页版只支持默认的涉害取法");
  }
  const [gan, zhi] = day;
  const off = mod(zi(monthGeneral) - zi(hour), 12);
  const up = (z) => shift(z, off);
  const down = (z) => shift(z, -off);

  const isDay = DAY_HOURS.includes(hour);
  const gui = GUIREN[school.guiren][gan][isDay ? 0 : 1];
  const step = SHUN_SEATS.includes(down(gui)) ? 1 : -1;
  const gen = (z) => GENERALS[mod((zi(z) - zi(gui)) * step, 12)];

  const j = JIGONG[gan];
  const k1 = [up(j), gan];
  const k2 = [up(k1[0]), k1[0]];
  const k3 = [up(zhi), zhi];
  const k4 = [up(k3[0]), k3[0]];

  const [gate, name, chuan] = lessonsTable[day][off];
  const kong = xunkong(day);

  return {
    format: "liuren-chart/1",
    engine: "liuren-web 0.1",
    input: { day, month_general: monthGeneral, hour },
    school: { ...school },
    plate: Object.fromEntries([...ZHI].map((z) => [z, up(z)])),
    generals: Object.fromEntries([...ZHI].map((z) => [z, gen(up(z))])),
    noble: { period: isDay ? "昼" : "夜", direction: step === 1 ? "顺" : "逆" },
    lessons: [k1, k2, k3, k4].map(([u, d]) => ({ up: u, down: d, general: gen(u) })),
    method: { gate, name },
    transmissions: [...chuan].map((z) => ({ branch: z, general: gen(z), kin: liuqin(gan, z), void: kong.includes(z) })),
    void: kong,
  };
}

// ---- 时间层：公历时间 → 干支、月将、占时 ----

const JIEQI_ORDER = ["春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
  "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰"];
const ZHONGQI_JIANG = { 雨水: "亥", 春分: "戌", 谷雨: "酉", 小满: "申", 夏至: "未", 大暑: "午",
  处暑: "巳", 秋分: "辰", 霜降: "卯", 小雪: "寅", 冬至: "丑", 大寒: "子" };
const JIE_JIAN = { 立春: "寅", 惊蛰: "卯", 清明: "辰", 立夏: "巳", 芒种: "午", 小暑: "未",
  立秋: "申", 白露: "酉", 寒露: "戌", 立冬: "亥", 大雪: "子", 小寒: "丑" };
const WUHU = { 甲: "丙", 己: "丙", 乙: "戊", 庚: "戊", 丙: "庚", 辛: "庚", 丁: "壬", 壬: "壬", 戊: "甲", 癸: "甲" };
const HOUR = 3600 * 1000;
const DAY_MS = 24 * HOUR;
const EPOCH_2000 = Date.UTC(2000, 0, 1) / DAY_MS;

export function jieqiTable(raw) {
  const first = JIEQI_ORDER.indexOf(raw.first);
  return { t: raw.t.map((s) => s * 1000), n: raw.t.map((_, i) => JIEQI_ORDER[(first + i) % 24]) };
}

const pad = (n, w = 2) => String(n).padStart(w, "0");

// 把"北京时间"意义下的毫秒数（UTC 毫秒 + 8 小时）格式化
function fmtShifted(ms) {
  const d = new Date(ms);
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())} ` +
    `${pad(d.getUTCHours())}:${pad(d.getUTCMinutes())}:${pad(d.getUTCSeconds())}`;
}
const fmtBJT = (utcMs) => fmtShifted(utcMs + 8 * HOUR);

// "2026-10-08 14:20" 或 "2026-10-08 14:20:05"（北京时间）→ UTC 毫秒
export function parseBJT(s) {
  const m = /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?$/.exec(s.trim());
  if (!m) throw new Error(`时间格式应为 2026-10-08 14:20：${s}`);
  const [, y, mo, d, h, mi, se] = m.map((x) => (x === undefined ? 0 : Number(x)));
  return Date.UTC(y, mo - 1, d, h - 8, mi, se || 0);
}

function last(tab, utcMs, names) {
  if (!(tab.t[0] <= utcMs && utcMs < tab.t[tab.t.length - 1])) throw new Error("超出节气表范围（1900–2100）");
  let lo = 0, hi = tab.t.length;               // bisect_right
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (utcMs < tab.t[mid]) hi = mid; else lo = mid + 1;
  }
  let i = lo - 1;
  while (!(tab.n[i] in names)) i--;
  return [tab.n[i], tab.t[i]];
}

// 均时差（分钟），与 core/liuren_core/timing.py 同一近似式
export function equationOfTime(utcMs) {
  const d = new Date(utcMs);
  const doy = Math.floor((Date.UTC(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate()) -
    Date.UTC(d.getUTCFullYear(), 0, 1)) / DAY_MS) + 1;
  const g = (2 * Math.PI / 365) * (doy - 1 + (d.getUTCHours() - 12) / 24);
  return 229.18 * (0.000075 + 0.001868 * Math.cos(g) - 0.032077 * Math.sin(g)
    - 0.014615 * Math.cos(2 * g) - 0.040849 * Math.sin(2 * g));
}

export function resolve(utcMs, tab, { zishi = "子初", true_solar = false, longitude = null } = {}) {
  // 本地时间（以"平移后的 UTC 毫秒"表示）：北京时间，或真太阳时
  let local;
  if (!true_solar) {
    local = utcMs + 8 * HOUR;
  } else {
    if (longitude === null || longitude === undefined) throw new Error("用真太阳时须给出经度");
    const minutes = longitude * 4 + equationOfTime(utcMs);
    // 与 Python 的 timedelta(minutes=…) 一致：先取整到微秒，再截到秒
    const us = utcMs * 1000 + Math.round(minutes * 60e6);
    local = Math.floor(us / 1e6) * 1000;
  }
  const lt = new Date(local);
  const h = lt.getUTCHours();
  const hour = ZHI[Math.floor((h + 1) / 2) % 12];
  let dayNum = Math.floor(local / DAY_MS);
  if (zishi === "子初" && h === 23) dayNum += 1;
  else if (zishi !== "子初" && zishi !== "子正") throw new Error(`子时换日只支持 子初 / 子正：${zishi}`);
  const day = JIAZI[mod(dayNum - EPOCH_2000 + 54, 60)];

  const [zq, zqT] = last(tab, utcMs, ZHONGQI_JIANG);
  const [jie] = last(tab, utcMs, JIE_JIAN);
  const lichunYear = new Date(last(tab, utcMs, { 立春: 1 })[1] + 8 * HOUR).getUTCFullYear();
  const yearGz = JIAZI[mod(lichunYear - 1984, 60)];
  const jian = JIE_JIAN[jie];
  const monthGan = GAN[mod(GAN.indexOf(WUHU[yearGz[0]]) + mod(zi(jian) - 2, 12), 10)];

  return {
    beijing: fmtBJT(utcMs),
    local: fmtShifted(local),
    true_solar,
    longitude: longitude ?? null,
    year: yearGz,
    month: monthGan + jian,
    day,
    hour,
    month_general: ZHONGQI_JIANG[zq],
    solar_term: { name: zq, at: fmtBJT(zqT) },
  };
}

export function castAt(utcMs, data, school = DEFAULT_SCHOOL, longitude = null) {
  const t = resolve(utcMs, data.jieqi, { zishi: school.zishi, true_solar: school.true_solar, longitude });
  const c = cast(t.day, t.month_general, t.hour, data.lessons, school);
  c.time = t;
  return c;
}

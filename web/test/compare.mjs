// 比对网页版 JS 与 Python 引擎：node web/test/compare.mjs fixtures.json
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { castAt, jieqiTable, parseBJT } from "../liuren.js";

const here = dirname(fileURLToPath(import.meta.url));
const data = {
  lessons: JSON.parse(readFileSync(join(here, "../data/lessons.json"), "utf8")),
  jieqi: jieqiTable(JSON.parse(readFileSync(join(here, "../data/jieqi.json"), "utf8"))),
};
const cases = JSON.parse(readFileSync(process.argv[2], "utf8"));

let bad = 0;
for (const c of cases) {
  const got = castAt(parseBJT(c.time), data, c.school, c.longitude);
  const want = { ...c.chart };
  delete want.engine;
  delete got.engine;
  const a = JSON.stringify(got), b = JSON.stringify(want);
  if (a !== b) {
    bad++;
    if (bad <= 5) {
      console.log(`✗ ${c.time} ${JSON.stringify(c.school)} ${c.longitude}`);
      for (const k of Object.keys(want)) {
        if (JSON.stringify(got[k]) !== JSON.stringify(want[k])) {
          console.log(`  ${k}\n    js: ${JSON.stringify(got[k])}\n    py: ${JSON.stringify(want[k])}`);
        }
      }
    }
  }
}
console.log(`${cases.length} 个时刻，不一致 ${bad} 个`);
process.exit(bad ? 1 : 0);

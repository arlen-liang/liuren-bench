"""与 kinliuren 逐课比对三传。kinliuren 不是依赖，需另行 clone：

    git clone https://github.com/kentang2017/kinliuren /tmp/kinliuren
    uv run python tools/diff_kinliuren.py /tmp/kinliuren/src

kinliuren 的三传会随绝对位置漂移，所以对每一课取它在 12 个绝对位置上给出的全部结果：
我们的结果落在其中任一个即算"部分一致"，与其全部一致才算"一致"。
"""

import sys
from collections import Counter

from liuren_core import cast
from liuren_core.base import JIAZI, ZHI

sys.path.insert(0, sys.argv[1])
from kinliuren.kinliuren import Liuren  # noqa: E402

MG_JQ = {"亥": "雨水", "戌": "春分", "酉": "穀雨", "申": "小滿", "未": "夏至", "午": "大暑",
         "巳": "處暑", "辰": "秋分", "卯": "霜降", "寅": "小雪", "丑": "冬至", "子": "大寒"}
GAN = "甲乙丙丁戊己庚辛壬癸"


def hour_gz(day, hz):
    start = {"甲": 0, "己": 0, "乙": 2, "庚": 2, "丙": 4, "辛": 4, "丁": 6, "壬": 6, "戊": 8, "癸": 8}
    return GAN[(start[day[0]] + ZHI.index(hz)) % 10] + hz


tally, rows = Counter(), []
for day in JIAZI:
    for off in range(12):
        ours = None
        theirs = Counter()
        for mg in ZHI:
            hz = ZHI[(ZHI.index(mg) - off) % 12]
            c = cast(day, mg, hz)
            ours = ours or ("".join(n["branch"] for n in c["transmissions"]), c["method"]["gate"] + "/" + c["method"]["name"])
            try:
                r = Liuren(MG_JQ[mg], "正", day, hour_gz(day, hz)).result(1)
                theirs["".join(v[0] for v in r["三傳"].values())] += 1
            except Exception:
                theirs["崩溃"] += 1
        if set(theirs) == {ours[0]}:
            tally["一致"] += 1
        else:
            tally["部分一致" if ours[0] in theirs else "不一致"] += 1
            rows.append((day, off, ours, dict(theirs)))

print(dict(tally))
by_method = Counter(r[2][1].split("/")[0] for r in rows if r[2][0] not in r[3])
print("不一致课按我方宗门：", dict(by_method))
for day, off, ours, theirs in rows:
    flag = "  " if ours[0] in theirs else "✗ "
    print(f"{flag}{day} 相对位{off:>2}  我方 {ours[0]} {ours[1]:<12} kinliuren {theirs}")

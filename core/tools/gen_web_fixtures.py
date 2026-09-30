"""为网页版比对测试生成样本：随机时刻（含子时、节气交接前后、真太阳时、两版贵人）的完整课盘。

    uv run python tools/gen_web_fixtures.py 1000 > fixtures.json
"""

import json
import random
import sys
from datetime import datetime, timedelta

from pathlib import Path

from liuren_core import School, cast_at
from liuren_core.timing import BJT, _table

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skill"))
from liuren_skill import build_prompt  # noqa: E402


def main(n: int):
    rnd = random.Random(20260930)
    ts, _ = _table()
    start, end = datetime(1901, 3, 1), datetime(2099, 11, 1)
    out = []
    for i in range(n):
        if i % 5 == 0:     # 节气交接前后几分钟，最容易出错
            t = rnd.choice(ts[40:-40]).astimezone(BJT).replace(tzinfo=None)
            dt = (t + timedelta(minutes=rnd.randint(-3, 3))).replace(second=0)
        elif i % 5 == 1:   # 子时前后
            dt = start + timedelta(days=rnd.randint(0, (end - start).days))
            dt = dt.replace(hour=rnd.choice([22, 23, 0]), minute=rnd.randint(0, 59))
        else:
            dt = start + timedelta(minutes=rnd.randint(0, int((end - start).total_seconds() // 60)))
        school = School(guiren=rnd.choice(["甲牛", "甲羊"]), zishi=rnd.choice(["子初", "子正"]),
                        true_solar=(i % 7 == 0))
        lon = round(rnd.uniform(73, 135), 2) if school.true_solar else None
        chart = cast_at(dt, school, longitude=lon)
        case = {"time": dt.strftime("%Y-%m-%d %H:%M"), "school": school.__dict__, "longitude": lon, "chart": chart}
        if school == School():          # 提示词只对默认流派（网页只用默认流派）
            case["prompt"] = build_prompt(chart, f"测试问题{i}：$1 {{{{chart}}}}", "2099-12-31")
        out.append(case)
    json.dump(out, sys.stdout, ensure_ascii=False)


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 1000)

"""生成节气表 liuren_core/data/jieqi.json：1900–2100 年每个节气的时刻（UTC，精确到秒）。

    uv run python tools/gen_jieqi.py

节气即太阳视黄经走到 15° 的整数倍（春分 0°、清明 15°……）。用 pyephem 求太阳的真黄经
（含章动、光行差），二分法逼近到 1 秒。运行时引擎只查这张表，不依赖 pyephem。
"""

import json
import math
from pathlib import Path

import ephem

NAMES = ["春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑", "白露",
         "秋分", "寒露", "霜降", "立冬", "小雪", "大雪", "冬至", "小寒", "大寒", "立春", "雨水", "惊蛰"]


def solar_lon(t: float) -> float:
    """t 时刻太阳视黄经（度，0–360），黄道取当日真黄道。"""
    d = ephem.Date(t)
    s = ephem.Sun()
    s.compute(d, epoch=d)
    # g_ra/g_dec 是地心视位置（含章动、光行差）；a_ra/a_dec 不含，会差出约 8 分钟
    app = ephem.Equatorial(s.g_ra, s.g_dec, epoch=d)
    return math.degrees(float(ephem.Ecliptic(app, epoch=d).lon)) % 360


def crossing(target: float, t0: float) -> float:
    """从 t0 起找太阳黄经首次到达 target 的时刻。"""
    step = 1.0
    diff = lambda t: ((solar_lon(t) - target + 180) % 360) - 180
    t = t0
    while diff(t) >= 0:          # 退到 target 之前
        t -= step
    while diff(t + step) < 0:    # 按天前进到跨过 target
        t += step
    lo, hi = t, t + step
    while (hi - lo) * 86400 > 0.5:
        mid = (lo + hi) / 2
        if diff(mid) < 0:
            lo = mid
        else:
            hi = mid
    return hi


def main():
    out = []
    t = float(ephem.Date("1899/12/1"))
    end = float(ephem.Date("2101/1/1"))
    k = round(solar_lon(t) / 15) % 24       # 从最近的节气开始
    while t < end:
        t = crossing(k * 15.0, t)
        d = ephem.Date(t).tuple()
        sec = int(round(d[5]))
        stamp = ephem.Date((d[0], d[1], d[2], d[3], d[4], sec))
        out.append([str(stamp.datetime().strftime("%Y-%m-%dT%H:%M:%SZ")), NAMES[k]])
        k = (k + 1) % 24
        t += 10
    path = Path(__file__).resolve().parents[1] / "liuren_core" / "data" / "jieqi.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    print(f"{len(out)} 个节气 → {path}")


if __name__ == "__main__":
    main()

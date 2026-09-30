"""时间层：公历时间 → 年月日干支、月将、占时。

- 节气时刻查 data/jieqi.json（1900–2100，由 tools/gen_jieqi.py 用 pyephem 生成，精确到秒）
- 月将按中气当刻换：雨水后亥将（登明），春分后戌将（河魁），依次逆行
- 年以立春、月以节为界
- 日干支按儒略日推算；子时换日与真太阳时是开关
"""

import bisect
import json
import math
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
from importlib import resources

from .base import GAN, JIAZI, ZHI

BJT = timezone(timedelta(hours=8))

# 中气 → 月将
ZHONGQI_JIANG = {"雨水": "亥", "春分": "戌", "谷雨": "酉", "小满": "申", "夏至": "未", "大暑": "午",
                 "处暑": "巳", "秋分": "辰", "霜降": "卯", "小雪": "寅", "冬至": "丑", "大寒": "子"}
# 节 → 月建
JIE_JIAN = {"立春": "寅", "惊蛰": "卯", "清明": "辰", "立夏": "巳", "芒种": "午", "小暑": "未",
            "立秋": "申", "白露": "酉", "寒露": "戌", "立冬": "亥", "大雪": "子", "小寒": "丑"}
# 五虎遁：年干 → 寅月月干
_WUHU = {"甲": "丙", "己": "丙", "乙": "戊", "庚": "戊", "丙": "庚", "辛": "庚",
         "丁": "壬", "壬": "壬", "戊": "甲", "癸": "甲"}

_ORD_2000 = date(2000, 1, 1).toordinal()   # 2000-01-01 为戊午日（六十甲子第 54）


@lru_cache(maxsize=1)
def _table():
    raw = json.loads(resources.files("liuren_core").joinpath("data/jieqi.json").read_text("utf-8"))
    ts = [datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) for s, _ in raw]
    return ts, [n for _, n in raw]


def _to_utc(dt: datetime) -> datetime:
    """无时区的时间一律当北京时间。"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=BJT)
    return dt.astimezone(timezone.utc)


def _last(utc: datetime, names) -> tuple[str, datetime]:
    """utc 时刻之前（含当刻）最近一个属于 names 的节气。"""
    ts, ns = _table()
    if not ts[0] <= utc < ts[-1]:
        raise ValueError(f"超出节气表范围（1900–2100）：{utc}")
    i = bisect.bisect_right(ts, utc) - 1
    while ns[i] not in names:
        i -= 1
    return ns[i], ts[i]


def day_ganzhi(d: date) -> str:
    return JIAZI[(d.toordinal() - _ORD_2000 + 54) % 60]


def equation_of_time(utc: datetime) -> float:
    """均时差（分钟，真太阳时 − 平太阳时），NOAA 近似式，误差约半分钟。"""
    doy = utc.timetuple().tm_yday
    g = 2 * math.pi / 365 * (doy - 1 + (utc.hour - 12) / 24)
    return 229.18 * (0.000075 + 0.001868 * math.cos(g) - 0.032077 * math.sin(g)
                     - 0.014615 * math.cos(2 * g) - 0.040849 * math.sin(2 * g))


def local_time(utc: datetime, true_solar: bool, longitude: float | None) -> datetime:
    """定占时用的本地时间：默认北京时间；真太阳时 = 经度折算的平太阳时 + 均时差。"""
    if not true_solar:
        return utc.astimezone(BJT).replace(tzinfo=None)
    if longitude is None:
        raise ValueError("用真太阳时须给出经度")
    minutes = longitude * 4 + equation_of_time(utc)
    return (utc + timedelta(minutes=minutes)).replace(tzinfo=None)


def resolve(dt: datetime, zishi: str = "子初", true_solar: bool = False,
            longitude: float | None = None) -> dict:
    """公历时间 → 起课所需的干支与月将。

    zishi："子初" 即 23 点换日（子时整个算次日）；"子正" 即 0 点换日。
    """
    utc = _to_utc(dt)
    lt = local_time(utc, true_solar, longitude)

    hour = ZHI[((lt.hour + 1) // 2) % 12]
    d = lt.date()
    if zishi == "子初" and lt.hour == 23:
        d += timedelta(days=1)
    elif zishi != "子正" and zishi != "子初":
        raise ValueError(f"子时换日只支持 子初 / 子正：{zishi}")

    zq, zq_t = _last(utc, ZHONGQI_JIANG)
    jie, jie_t = _last(utc, JIE_JIAN)
    lichun_year = _last(utc, {"立春"})[1].astimezone(BJT).year
    year_gz = JIAZI[(lichun_year - 1984) % 60]
    jian = JIE_JIAN[jie]
    month_gan = GAN[(GAN.index(_WUHU[year_gz[0]]) + (ZHI.index(jian) - 2) % 12) % 10]

    return {
        "beijing": utc.astimezone(BJT).strftime("%Y-%m-%d %H:%M:%S"),
        "local": lt.strftime("%Y-%m-%d %H:%M:%S"),
        "true_solar": true_solar,
        "longitude": longitude,
        "year": year_gz,
        "month": month_gan + jian,
        "day": day_ganzhi(d),
        "hour": hour,
        "month_general": ZHONGQI_JIANG[zq],
        "solar_term": {"name": zq, "at": zq_t.astimezone(BJT).strftime("%Y-%m-%d %H:%M:%S")},
    }

"""起课：日干支 + 月将 + 占时 → 课盘；或直接按公历时间起课。"""

from datetime import datetime

from .base import GENERALS, JIAZI, ZHI, liuqin, xunkong, zi
from .sanchuan import Pan, derive, sike
from .school import DEFAULT, GUIREN_TABLES, School
from .timing import resolve

_DAY_HOURS = set("卯辰巳午未申")      # 卯酉分界下的昼时
_SHUN_SEATS = set("亥子丑寅卯辰")     # 贵人临此六位顺布，余逆布


def _generals(day: str, hour: str, pan: Pan, school: School) -> dict:
    """十二天将：按昼夜取贵人，贵人所临地盘在亥至辰则顺布，否则逆布。"""
    if school.daynight != "卯酉":
        raise NotImplementedError(f"昼夜分界 {school.daynight} 尚未实现")
    is_day = hour in _DAY_HOURS
    gui = GUIREN_TABLES[school.guiren][day[0]][0 if is_day else 1]
    step = 1 if pan.down(gui) in _SHUN_SEATS else -1
    return {z: GENERALS[((zi(z) - zi(gui)) * step) % 12] for z in ZHI}, is_day, step


def cast(day: str, yuejiang: str, hour: str, school: School = DEFAULT) -> dict:
    """起一课。

    day: 日干支，如 "甲子"；yuejiang: 月将地支，如 "亥"；hour: 占时地支，如 "午"。
    返回 dict，字段即课盘数据格式草案（v0，M1 定稿为 v1）。
    """
    if day not in JIAZI:
        raise ValueError(f"不是六十甲子：{day}")
    if yuejiang not in ZHI or hour not in ZHI:
        raise ValueError(f"月将、占时须为地支：{yuejiang} {hour}")

    pan = Pan(yuejiang, hour)
    ks = sike(day, pan)
    res = derive(day, pan, school)
    gen, is_day, step = _generals(day, hour, pan, school)
    kong = xunkong(day)

    def node(z):
        return {"支": z, "将": gen[z], "亲": liuqin(day[0], z), "空": z in kong}

    return {
        "输入": {"日": day, "月将": yuejiang, "占时": hour},
        "流派": {"贵人": school.guiren, "昼夜": school.daynight, "涉害": school.shehai,
                 "涉害计寄干": school.shehai_count_gan, "子时换日": school.zishi,
                 "真太阳时": school.true_solar},
        "天地盘": {z: pan.up(z) for z in ZHI},          # 地盘 → 天盘
        "天将": {z: gen[pan.up(z)] for z in ZHI},       # 地盘位 → 其上天盘所乘之将
        "贵人": {"昼夜": "昼" if is_day else "夜", "顺逆": "顺" if step == 1 else "逆"},
        "四课": [{"上": k.up, "下": k.down, "将": gen[k.up]} for k in ks],
        "课体": {"宗门": res.method, "课名": res.sub},
        "三传": [node(z) for z in res.chuan],
        "旬空": list(kong),
    }


def cast_at(dt: datetime, school: School = DEFAULT, longitude: float | None = None) -> dict:
    """按公历时间起课。无时区的 dt 当北京时间；用真太阳时须在 school 里打开并给经度。"""
    t = resolve(dt, school.zishi, school.true_solar, longitude)
    c = cast(t["日"], t["月将"], t["占时"], school)
    c["时间"] = t
    return c

"""时间层：干支锚点、节气交接、子时换日、真太阳时。"""

from datetime import date, datetime, timedelta, timezone

import pytest

from liuren_core import School, cast, cast_at
from liuren_core.timing import _table, day_ganzhi, equation_of_time, resolve

BJT = timezone(timedelta(hours=8))


def test_day_anchors():
    assert day_ganzhi(date(1949, 10, 1)) == "甲子"
    assert day_ganzhi(date(2000, 1, 1)) == "戊午"
    assert day_ganzhi(date(2008, 8, 8)) == "庚辰"


def test_year_month_anchor():
    t = resolve(datetime(2008, 8, 8, 20, 0))
    assert (t["年"], t["月"], t["日"]) == ("戊子", "庚申", "庚辰")


def test_jieqi_table_spotcheck():
    """与天文台公布时刻（北京时间，到分）比对。"""
    ts, ns = _table()
    got = {(n, t.astimezone(BJT).strftime("%Y-%m-%d %H:%M")) for t, n in zip(ts, ns)}
    for n, s in [("春分", "2024-03-20 11:06"), ("夏至", "2024-06-21 04:51"),
                 ("冬至", "2025-12-21 23:02"), ("立春", "2026-02-04 04:01")]:
        assert (n, s) in got, (n, s)
    assert len(ts) > 4800


def test_lichun_changes_year():
    before = resolve(datetime(2026, 2, 4, 4, 1, 0))
    after = resolve(datetime(2026, 2, 4, 4, 2, 0))
    assert (before["年"], before["月"]) == ("乙巳", "己丑")
    assert (after["年"], after["月"]) == ("丙午", "庚寅")


def test_yuejiang_changes_at_zhongqi_moment():
    # 2026 雨水 北京时间 02-18 23:51:43
    assert resolve(datetime(2026, 2, 18, 23, 51, 42))["月将"] == "子"
    assert resolve(datetime(2026, 2, 18, 23, 51, 44))["月将"] == "亥"


def test_all_twelve_generals_in_a_year():
    seen = {resolve(datetime(2026, 1, 1) + timedelta(days=d))["月将"] for d in range(0, 365, 5)}
    assert len(seen) == 12


def test_zishi():
    late = datetime(2026, 9, 30, 23, 30)
    assert resolve(late)["占时"] == "子"
    assert resolve(late, zishi="子初")["日"] == day_ganzhi(date(2026, 10, 1))
    assert resolve(late, zishi="子正")["日"] == day_ganzhi(date(2026, 9, 30))
    assert resolve(datetime(2026, 9, 30, 0, 30), zishi="子正")["日"] == day_ganzhi(date(2026, 9, 30))


def test_hours():
    for h, z in [(0, "子"), (1, "丑"), (3, "寅"), (11, "午"), (12, "午"), (13, "未"), (22, "亥"), (23, "子")]:
        assert resolve(datetime(2026, 9, 30, h, 10))["占时"] == z


def test_equation_of_time():
    # 均时差：11 月初约 +16.4 分，2 月中约 −14.2 分
    assert equation_of_time(datetime(2026, 11, 3, 4, tzinfo=timezone.utc)) == pytest.approx(16.4, abs=1)
    assert equation_of_time(datetime(2026, 2, 11, 4, tzinfo=timezone.utc)) == pytest.approx(-14.2, abs=1)


def test_true_solar():
    # 乌鲁木齐（东经约 87.6°）北京时间 12:00，平太阳时约早 2 小时 10 分，落在巳时
    t = resolve(datetime(2026, 9, 30, 12, 0), true_solar=True, longitude=87.6)
    assert t["占时"] == "巳"
    with pytest.raises(ValueError):
        resolve(datetime(2026, 9, 30, 12, 0), true_solar=True)


def test_timezone_aware_input():
    utc = datetime(2026, 9, 30, 6, 20, tzinfo=timezone.utc)      # 即北京时间 14:20
    assert resolve(utc) == resolve(datetime(2026, 9, 30, 14, 20))


def test_cast_at_matches_cast():
    c = cast_at(datetime(2026, 9, 30, 14, 20))
    t = c["时间"]
    base = cast(t["日"], t["月将"], t["占时"])
    assert c["三传"] == base["三传"] and c["四课"] == base["四课"]
    assert c["流派"]["子时换日"] == "子初"
    s = School(true_solar=True)
    assert cast_at(datetime(2026, 9, 30, 14, 20), s, longitude=116.4)["时间"]["起课时间"].endswith("（真太阳时）")


def test_out_of_range():
    with pytest.raises(ValueError):
        resolve(datetime(1890, 1, 1))

"""结构性检验：不依赖任何流派，对全部课逐一跑。"""

from collections import defaultdict

import pytest

from liuren_core import cast
from liuren_core.base import JIAZI, ZHI, ke

ALL = [(d, y, h) for d in JIAZI for y in ZHI for h in ZHI]   # 8640 次起课 = 720 课 × 12 个绝对位置


def _offset(y, h):
    return (ZHI.index(y) - ZHI.index(h)) % 12


@pytest.fixture(scope="module")
def charts():
    return {a: cast(*a) for a in ALL}


def test_no_crash_and_shape(charts):
    for a, c in charts.items():
        assert len(c["transmissions"]) == 3, a
        assert all(n["branch"] in ZHI for n in c["transmissions"]), a


def test_translation_invariance(charts):
    """六壬 720 课：同一日干支、同一"月将−占时"相对位，四课、三传、课体必须完全相同。"""
    seen = defaultdict(set)
    for (d, y, h), c in charts.items():
        key = (tuple((k["up"], k["down"]) for k in c["lessons"]),
               tuple(n["branch"] for n in c["transmissions"]),
               (c["method"]["gate"], c["method"]["name"]))
        seen[(d, _offset(y, h))].add(key)
    bad = {k: v for k, v in seen.items() if len(v) > 1}
    assert len(seen) == 720
    assert not bad, list(bad.items())[:3]


def test_fuyin_fanyin_counts(charts):
    one = {(d, _offset(y, h)): c for (d, y, h), c in charts.items()}
    methods = [c["method"]["gate"] for (d, off), c in one.items()]
    assert sum(1 for (d, off) in one if off == 0) == 60
    assert all(one[(d, 0)]["method"]["gate"] == "伏吟" for d in JIAZI)
    assert all(one[(d, 6)]["method"]["gate"] == "返吟" for d in JIAZI)
    assert methods.count("伏吟") == 60 and methods.count("返吟") == 60
    # 返吟无克只有丁丑、丁未、己丑、己未、辛丑、辛未六日
    jinglan = sorted(d for d in JIAZI if one[(d, 6)]["method"]["name"] == "井栏射")
    assert jinglan == sorted(["丁丑", "丁未", "己丑", "己未", "辛丑", "辛未"])


def test_single_zei_is_chongshen(charts):
    """贼克首法：四课下贼上仅一神（按上神去重）者，必为重审且取该神发用。"""
    for (d, y, h), c in charts.items():
        off = _offset(y, h)
        if off in (0, 6) or y != "亥":
            continue
        ks = c["lessons"]
        seat = lambda k: k["down"]
        zei = {k["up"] for k in ks if ke(seat(k), k["up"])}
        if len(zei) == 1:
            assert c["method"] == {"gate": "贼克", "name": "重审"}, (d, h)
            assert c["transmissions"][0]["branch"] == next(iter(zei)), (d, h)
